import customtkinter as ctk
import tkinter as tk
from .student_webcam import StudentWebcamOverlay
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from .network_utils import send_command
from .screen_receiver import ScreenViewer

# Import hiwalay na modules mula sa kaparehong folder
from .history_window import open_history_window
from .student_cards import setup_grid_layout, create_student_card
from .network_listeners import start_global_listener as run_global_listener, update_thumbnail_frame, record_login, record_logout
from .account_approvals import open_account_approvals
from .dialogs import (
    open_text_message_dialog, 
    open_single_text_message_dialog, 
    open_website_dialog, 
    open_single_website_dialog
)
from .teacher_broadcast import toggle_teacher_broadcast

class TeacherDashboard(ctk.CTkToplevel):
    def __init__(self, master_app):
        super().__init__()
        self.master_app = master_app
        self.connected_students = {}
        self.student_cards = {}
        self.login_history_data = []
        self.active_viewers = {}  
        self.is_broadcasting_demo = False  
        self.btn_fullscreen_demo = None  
        
        self.title("Teacher Dashboard")
        self.geometry("1200x800")
        
        # --- TOP TOOLBAR ---
        self.top_toolbar = ctk.CTkFrame(self, height=65, fg_color="#333333", corner_radius=0)
        self.top_toolbar.pack(side="top", fill="x")
        
        toolbar_items = [
            ("Monitoring", None),
            ("Fullscreen demo", lambda: toggle_teacher_broadcast(self)),
            ("Window demo", None),
            ("Lock", self.lock_all_students),
            ("Unlock", self.unlock_all_students),
            ("Power on", None),
            ("Reboot", self.reboot_all_students),
            ("Power down", self.shutdown_all_students),
            ("Sleep", self.sleep_all_students),
            ("Logout user", None),
            ("Text message", lambda: open_text_message_dialog(self)),
            ("Run program", None),
            ("Open website", lambda: open_website_dialog(self)),
            ("Screenshot", None),
            ("History", lambda: open_history_window(self, self.login_history_data)),
            ("Approvals", lambda: open_account_approvals(self)),
            ("Refresh", self.refresh_connections),
        ]
        
        for btn_text, btn_command in toolbar_items:
            fg_col = "#1f6aa5" if btn_text == "Refresh" else "#383838"
            hover_col = "#144870" if btn_text == "Refresh" else "#505050"
            
            btn = ctk.CTkButton(
                self.top_toolbar,
                text=btn_text,
                image=None,
                compound="top",
                width=75,
                height=50,
                fg_color=fg_col,
                hover_color=hover_col,
                font=ctk.CTkFont(size=10),
                command=btn_command if btn_command else lambda t=btn_text: print(f"{t} clicked")
            )
            btn.pack(side="left", padx=1, pady=5)
            
            if btn_text == "Fullscreen demo":
                self.btn_fullscreen_demo = btn

        # --- MAIN GRID PARA SA MGA PC NG ESTUDYANTE ---
        setup_grid_layout(self)
        
        run_global_listener(self)
        self.start_teacher_broadcaster()

        # --- BOTTOM STATUS BAR ---
        self.bottom_bar = ctk.CTkFrame(self, height=40, fg_color="#2b2b2b", corner_radius=0)
        self.bottom_bar.pack(side="bottom", fill="x")
        
        self.lbl_rooms = ctk.CTkButton(self.bottom_bar, text="Computer rooms", fg_color="transparent", text_color="white", width=100)
        self.lbl_rooms.pack(side="left", padx=10)
        
        self.lbl_screenshots = ctk.CTkButton(self.bottom_bar, text="Screenshots", fg_color="transparent", text_color="white", width=90)
        self.lbl_screenshots.pack(side="left", padx=5)
        
        self.search_entry = ctk.CTkEntry(self.bottom_bar, placeholder_text="Search users and computers", width=220)
        self.search_entry.pack(side="left", padx=15, pady=5)

    def show_notification(self, message):
        pass

    def start_teacher_broadcaster(self):
        pass

    def refresh_connections(self):
        print("[DEBUG] Nirerefresh ang student cards sa dashboard...")
        for ip, card_info in list(self.student_cards.items()):
            try:
                if isinstance(card_info, dict) and "frame" in card_info:
                    card_info["frame"].destroy()
                elif hasattr(card_info, "destroy"):
                    card_info.destroy()
            except Exception as e:
                print(f"Error sa pagbura ng card para sa {ip}: {e}")
                
        self.student_cards.clear()
        self.connected_students.clear()
        print("[DEBUG] Refresh tapos na.")

    def setup_grid_layout(self):
        setup_grid_layout(self)

    def create_student_card(self, name, ip, index):
        create_student_card(self, name, ip, index)

    def update_thumbnail_frame(self, ip, img_tk):
        update_thumbnail_frame(self, ip, img_tk)

    def show_context_menu(self, event, ip, name):
        context_menu = tk.Menu(self, tearoff=0, bg="#f0f0f0", fg="black", font=("Arial", 10))
        context_menu.add_command(label="Remote View", command=lambda: self.open_full_view(ip, is_control=False))
        
        if self.is_broadcasting_demo:
            context_menu.add_command(label="Stop demo", command=lambda: toggle_teacher_broadcast(self))
        else:
            context_menu.add_command(label="Fullscreen demo", command=lambda: toggle_teacher_broadcast(self))
            
        context_menu.add_separator()
        context_menu.add_command(label="Lock", command=lambda: send_command(ip, "LOCK"))
        context_menu.add_command(label="Unlock", command=lambda: send_command(ip, "UNLOCK"))
        context_menu.add_separator()
        context_menu.add_command(label="Message", command=lambda: open_single_text_message_dialog(self, ip))
        context_menu.add_separator()
        context_menu.add_command(label="Open website", command=lambda: open_single_website_dialog(self, ip))
        context_menu.add_separator()
        context_menu.add_command(label="Reboot", command=lambda: send_command(ip, "REBOOT"))
        context_menu.add_command(label="Sleep", command=lambda: send_command(ip, "SLEEP"))
        context_menu.add_command(label="Power down", command=lambda: send_command(ip, "SHUTDOWN"))
        context_menu.add_separator()
        context_menu.add_command(label="Remote Control", command=lambda: self.open_full_view(ip, is_control=True))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def open_full_view(self, student_ip, is_control=False):
        try:
            if student_ip in self.active_viewers:
                try:
                    self.active_viewers[student_ip].destroy()
                except:
                    pass
            
            viewer = ScreenViewer(student_ip, control_mode=is_control)
            self.active_viewers[student_ip] = viewer
            
            def on_viewer_close():
                if student_ip in self.active_viewers:
                    del self.active_viewers[student_ip]
                viewer.destroy()
                
            viewer.protocol("WM_DELETE_WINDOW", on_viewer_close)
        except Exception as e:
            print(f"Error sa pagbubukas ng ScreenViewer: {e}")

    def record_login(self, name, ip):
        record_login(self, name, ip)

    def record_logout(self, ip):
        record_logout(self, ip)

    def start_global_listener(self):
        run_global_listener(self)

    def lock_all_students(self):
        for ip in self.student_cards.keys():
            send_command(ip, "LOCK")

    def unlock_all_students(self):
        for ip in self.student_cards.keys():
            send_command(ip, "UNLOCK")

    def reboot_all_students(self):
        for ip in self.student_cards.keys():
            send_command(ip, "REBOOT")

    def shutdown_all_students(self):
        for ip in self.student_cards.keys():
            send_command(ip, "SHUTDOWN")

    def sleep_all_students(self):
        for ip in self.student_cards.keys():
            send_command(ip, "SLEEP")