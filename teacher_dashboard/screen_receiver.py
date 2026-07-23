import customtkinter as ctk
import tkinter as tk
import threading, io
import socket
from datetime import datetime
from PIL import Image, ImageTk, ImageFile
from .network_utils import send_control_command

ImageFile.LOAD_TRUNCATED_IMAGES = True

class ScreenViewer(ctk.CTkToplevel):
    def __init__(self, student_ip, control_mode=False):
        super().__init__()
        self.student_ip = student_ip
        self.control_mode = control_mode  # False = Remote View, True = Remote Control
        
        # Baguhin ang title batay sa pinindot
        mode_title = "Remote Control" if self.control_mode else "Remote View"
        self.title(f"{mode_title} - {student_ip}")
        self.attributes("-fullscreen", True)
        
        self.latest_image = None
        self.running = True
        self.conn = None
        
        # Grid Configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.label = tk.Label(self, bg="black")
        self.label.grid(row=0, column=0, sticky="nsew")
        
        # --- TOP CONTROLS OVERLAY ---
        self.top_control_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=6)
        self.top_control_frame.place(relx=0.98, rely=0.02, anchor="ne")

        self.btn_screenshot = ctk.CTkButton(
            self.top_control_frame, text="Screenshot", width=90, height=30,
            fg_color="#383838", hover_color="#505050", command=self.take_screenshot
        )
        self.btn_screenshot.pack(side="left", padx=5, pady=5)
       
        self.btn_exit = ctk.CTkButton(
            self.top_control_frame, text="Exit", width=70, height=30,
            fg_color="#A83232", hover_color="#C84242", command=self.on_closing
        )
        self.btn_exit.pack(side="left", padx=5, pady=5)
       
        self.bind("<Escape>", lambda e: self.on_closing())
        self.label.bind("<Configure>", self.on_resize)
        
        # I-activate lamang ang mouse control kung Remote Control ang pinili
        if self.control_mode:
            self.setup_mouse_control()
        
        # Simulan ang hiwalay na listener sa Port 9997 para sa live stream
        threading.Thread(target=self.start_stream_listener, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_stream_listener(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(("0.0.0.0", 9997))
            server.listen(1)
            server.settimeout(1.0)
            
            while self.running:
                try:
                    conn, addr = server.accept()
                    if addr[0] == self.student_ip:
                        self.conn = conn
                        # Simulan ang START_CONTROL kapag Remote Control mode lang
                        if self.control_mode:
                            try:
                                send_control_command(self.student_ip, "START_CONTROL")
                            except:
                                pass
                        self.receive_stream()
                        break
                    else:
                        conn.close()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"Stream listener error: {e}")
        finally:
            server.close()

    def receive_stream(self):
        while self.running and self.conn:
            try:
                self.conn.settimeout(3.0)
                header = self.conn.recv(4)
                if not header: break
                size = int.from_bytes(header, byteorder='big')
                
                if size <= 0 or size > 10 * 1024 * 1024:
                    break
                
                img_data = bytearray()
                while len(img_data) < size and self.running:
                    packet = self.conn.recv(min(size - len(img_data), 65536))
                    if not packet: break
                    img_data.extend(packet)
                
                if len(img_data) == size and self.running:
                    try:
                        image = Image.open(io.BytesIO(img_data))
                        image.load() 
                        self.latest_image = image
                        self.after(0, lambda img=image: self.display_image(img))
                    except Exception:
                        pass 
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Stream loop error: {e}")
                break

    def on_resize(self, event):
        if self.latest_image:
            self.display_image(self.latest_image)

    def display_image(self, pil_image):
        new_width = self.label.winfo_width()
        new_height = self.label.winfo_height()
        if new_width > 1 and new_height > 1:
            try:
                resized_img = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_img)
                self.label.config(image=photo)
                self.label.image = photo
            except Exception:
                pass

    def take_screenshot(self):
        try:
            if self.latest_image:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{self.student_ip}_{timestamp}.png"
                self.latest_image.save(filename)
                print(f"Screenshot saved as {filename}")
        except Exception as e:
            print(f"Error taking screenshot: {e}")

    def on_closing(self):
        self.running = False
        # Itigil ang control kapag nasa Remote Control mode at pinindot ang Exit
        if self.control_mode:
            try:
                send_control_command(self.student_ip, "STOP_CONTROL")
            except:
                pass
        if self.conn:
            try: self.conn.close()
            except: pass
        self.destroy()

    def setup_mouse_control(self):
        self.label.bind("<Motion>", self.on_mouse_move)
        self.label.bind("<B1-Motion>", self.on_mouse_move)
        self.label.bind("<Button-1>", lambda e: self.send_mouse("CLICK"))

    def on_mouse_move(self, event):
        if self.control_mode:
            send_control_command(self.student_ip, f"MOVE:{event.x}:{event.y}")

    def send_mouse(self, command):
        if self.control_mode:
            send_control_command(self.student_ip, command)