import customtkinter as ctk
import tkinter as tk
from .network_utils import send_command
from .screen_receiver import ScreenViewer

# Import hiwalay na modules mula sa kaparehong folder
from .history_window import open_history_window
from .student_cards import setup_grid_layout, create_student_card
from .network_listeners import start_global_listener as run_global_listener, update_thumbnail_frame, record_login, record_logout
from .account_approvals import open_account_approvals

class TeacherDashboard(ctk.CTkToplevel):
    def __init__(self, master_app):
        super().__init__()
        self.master_app = master_app
        self.connected_students = {}
        self.student_cards = {}
        self.login_history_data = []
        
        self.title("Teacher Dashboard")
        self.geometry("1200x800")
        
        # --- TOP TOOLBAR ---
        self.top_toolbar = ctk.CTkFrame(self, height=65, fg_color="#333333", corner_radius=0)
        self.top_toolbar.pack(side="top", fill="x")
        
        toolbar_items = [
            ("Monitoring", None),
            ("Fullscreen demo", None),
            ("Window demo", None),
            ("Lock", self.lock_all_students),
            ("Unlock", self.unlock_all_students),
            ("Power on", None),
            ("Reboot", lambda: send_command("192.168.100.251", "REBOOT")),
            ("Power down", lambda: send_command("192.168.100.251", "SHUTDOWN")),
            ("Sleep", lambda: send_command("192.168.100.251", "SLEEP")),
            ("Logout user", None),
            ("Text message", self.open_text_message_dialog),
            ("Run program", None),
            ("Open website", self.open_website_dialog),
            ("Screenshot", None),
            ("History", lambda: open_history_window(self, self.login_history_data)),
            ("Approvals", lambda: open_account_approvals(self)),
        ]
        
        for btn_text, btn_command in toolbar_items:
            btn = ctk.CTkButton(
                self.top_toolbar,
                text=btn_text,
                image=None,
                compound="top",
                width=75,
                height=50,
                fg_color="#383838",
                hover_color="#505050",
                font=ctk.CTkFont(size=10),
                command=btn_command if btn_command else lambda t=btn_text: print(f"{t} clicked")
            )
            btn.pack(side="left", padx=1, pady=5)

        # --- MAIN GRID PARA SA MGA PC NG ESTUDYANTE ---
        setup_grid_layout(self)
        
        # Direktang pinapagana ang listener para sa Port 5001 at 9998
        run_global_listener(self)

        # --- BOTTOM STATUS BAR ---
        self.bottom_bar = ctk.CTkFrame(self, height=40, fg_color="#2b2b2b", corner_radius=0)
        self.bottom_bar.pack(side="bottom", fill="x")
        
        self.lbl_rooms = ctk.CTkButton(self.bottom_bar, text="Computer rooms", fg_color="transparent", text_color="white", width=100)
        self.lbl_rooms.pack(side="left", padx=10)
        
        self.lbl_screenshots = ctk.CTkButton(self.bottom_bar, text="Screenshots", fg_color="transparent", text_color="white", width=90)
        self.lbl_screenshots.pack(side="left", padx=5)
        
        self.search_entry = ctk.CTkEntry(self.bottom_bar, placeholder_text="Search users and computers", width=220)
        self.search_entry.pack(side="left", padx=15, pady=5)

    def setup_grid_layout(self):
        setup_grid_layout(self)

    def create_student_card(self, name, ip, index):
        create_student_card(self, name, ip, index)

    def update_thumbnail_frame(self, ip, img_tk):
        update_thumbnail_frame(self, ip, img_tk)

    def show_context_menu(self, event, ip, name):
        context_menu = tk.Menu(self, tearoff=0, bg="#f0f0f0", fg="black", font=("Arial", 10))
        
        context_menu.add_command(label="Remote View", command=lambda: self.open_full_view(ip, is_control=False))
        context_menu.add_command(label="Fullscreen demo", command=lambda: print(f"Fullscreen demo for {ip}"))
        context_menu.add_separator()
        context_menu.add_command(label="Lock", command=lambda: send_command(ip, "LOCK"))
        context_menu.add_command(label="Unlock", command=lambda: send_command(ip, "UNLOCK"))
        context_menu.add_separator()
        
        context_menu.add_command(label="Message", command=lambda: self.open_single_text_message_dialog(ip))
        context_menu.add_separator()

        context_menu.add_command(label="Open website", command=lambda: self.open_single_website_dialog(ip))
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

    def open_text_message_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Send Text Message to Students")
        dialog.geometry("400x250")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text="I-type ang mensahe para sa mga estudyante:", font=("Arial", 12, "bold")).pack(pady=15)
        
        msg_entry = ctk.CTkTextbox(dialog, width=350, height=100)
        msg_entry.pack(pady=5)
        
        def send_msg():
            message = msg_entry.get("1.0", "end-1c").strip()
            if message:
                send_command("192.168.100.251", f"MSG:{message}")
                dialog.destroy()
                
        ctk.CTkButton(dialog, text="Broadcast Message", fg_color="green", command=send_msg).pack(pady=15)

    def open_single_text_message_dialog(self, ip):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Send Message to {ip}")
        dialog.geometry("400x250")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text=f"I-type ang mensahe para sa PC ({ip}):", font=("Arial", 12, "bold")).pack(pady=15)
        
        msg_entry = ctk.CTkTextbox(dialog, width=350, height=100)
        msg_entry.pack(pady=5)
        
        def send_single_msg():
            message = msg_entry.get("1.0", "end-1c").strip()
            if message:
                send_command(ip, f"MSG:{message}")
                dialog.destroy()
                
        ctk.CTkButton(dialog, text="Send Message", fg_color="green", command=send_single_msg).pack(pady=15)

    def open_website_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Open Website on All Students")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text="I-type ang URL (hal. https://www.facebook.com):", font=("Arial", 12, "bold")).pack(pady=15)
        
        url_entry = ctk.CTkEntry(dialog, width=350, placeholder_text="https://...")
        url_entry.pack(pady=5)
        
        def send_url():
            url = url_entry.get().strip()
            if url:
                send_command("192.168.100.251", f"URL:{url}")
                dialog.destroy()
                
        ctk.CTkButton(dialog, text="Open Website", fg_color="green", command=send_url).pack(pady=15)

    def open_single_website_dialog(self, ip):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Open Website on {ip}")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text=f"I-type ang URL para sa PC ({ip}):", font=("Arial", 12, "bold")).pack(pady=15)
        
        url_entry = ctk.CTkEntry(dialog, width=350, placeholder_text="https://...")
        url_entry.pack(pady=5)
        
        def send_single_url():
            url = url_entry.get().strip()
            if url:
                send_command(ip, f"URL:{url}")
                dialog.destroy()
                
        ctk.CTkButton(dialog, text="Open Website", fg_color="green", command=send_single_url).pack(pady=15)

    def open_full_view(self, student_ip, is_control=False):
        try:
            ScreenViewer(student_ip, control_mode=is_control)
        except Exception as e:
            print(f"Error sa pagbubukas ng ScreenViewer: {e}")

    def record_login(self, name, ip):
        record_login(self, name, ip)

    def record_logout(self, ip):
        record_logout(self, ip)

    def start_global_listener(self):
        run_global_listener(self)

    def lock_all_students(self):
        send_command("192.168.100.251", "LOCK")

    def unlock_all_students(self):
        send_command("192.168.100.251", "UNLOCK")