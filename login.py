import customtkinter as ctk
import json
import os
import socket
import threading
import datetime
import struct
import time
import cv2
import numpy as np
import pyautogui
from config import apply_theme
from teacher_dashboard.teacher_dash import TeacherDashboard
from teacher_dashboard.network_listeners import handle_student_expression  # <--- Na-import na rito
from admin_dashboard.admin_dash import AdminDashboard

apply_theme()

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScholarNet Login - Teacher/Admin")
        self.geometry("350x450")
        
        self.USERS = {
            "student": {"password": "student123", "role": "Student"},
            "teacher": {"password": "teacher123", "role": "Teacher"},
            "admin": {"password": "admin123", "role": "Admin"}
        }
        
        self.all_logs = [] 
        self.active_broadcast = False
        self.broadcast_socket = None
        self.active_teacher_dashboard = None  # <--- Reference para sa student expressions
        
        # Simulan ang background log listener at broadcast server
        threading.Thread(target=self.start_log_listener, daemon=True).start()
        threading.Thread(target=self.broadcast_stream_server, daemon=True).start()
        
        ctk.CTkLabel(self, text="ScholarNet Login", font=("Arial", 20, "bold")).pack(pady=20)
        self.user_entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.user_entry.pack(pady=10)
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.pass_entry.pack(pady=10)
        self.btn_login = ctk.CTkButton(self, text="Login", command=self.check_login)
        self.btn_login.pack(pady=20)
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack()

    def start_log_listener(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 5001))
        server.listen(5)
        print("==========================================")
        print("[DEBUG] Log & Command listener ay BUKAS sa port 5001")
        print("==========================================")
        while True:
            try:
                conn, addr = server.accept()
                data = conn.recv(1024).decode()
                
                if "ACTION: LOGIN_CHECK" in data:
                    self.handle_login_check(conn, data)
                elif "ACTION: REGISTER" in data:
                    self.process_register(data)
                    conn.close()
                elif "EXPRESSION:" in data:
                    # Masalo ang expression galing sa student at ipasa sa teacher dashboard
                    expr_content = data.replace("EXPRESSION:", "").strip()
                    print(f"[STUDENT EXPRESSION] mula {addr[0]}: {expr_content}")
                    if self.active_teacher_dashboard:
                        self.active_teacher_dashboard.after(
                            0, lambda e=expr_content, ip=addr[0]: handle_student_expression(self.active_teacher_dashboard, e, ip)
                        )
                    conn.close()
                else:
                    self.process_log(data)
                    conn.close()
            except: 
                break

    def handle_login_check(self, conn, data):
        try:
            parts = data.split("|")
            username = ""
            password = ""
            for part in parts:
                if "USER:" in part:
                    username = part.split("USER:")[1].strip()
                elif "PWD:" in part:
                    password = part.split("PWD:")[1].strip()
            
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            user_file_path = os.path.join(BASE_DIR, "users.json")
            
            users_data = {}
            if os.path.exists(user_file_path):
                with open(user_file_path, "r") as f:
                    try: users_data = json.load(f)
                    except: users_data = {}
            
            if username in users_data and users_data[username]["password"] == password:
                conn.send("SUCCESS".encode())
            else:
                conn.send("FAILED".encode())
        except Exception as e:
            print(f"[ERROR sa login check]: {e}")
            conn.send("FAILED".encode())
        finally:
            conn.close()

    def process_register(self, data):
        try:
            parts = data.split("|")
            username = ""
            password = ""
            for part in parts:
                if "USER:" in part:
                    username = part.split("USER:")[1].strip()
                elif "PWD:" in part:
                    password = part.split("PWD:")[1].strip()
            
            if username and password:
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                reg_file = os.path.join(BASE_DIR, "pending_accounts.json")
                
                account_data = []
                if os.path.exists(reg_file):
                    with open(reg_file, "r") as f:
                        try: account_data = json.load(f)
                        except: account_data = []
                
                if not any(acc["username"] == username for acc in account_data):
                    account_data.append({"username": username, "password": password, "status": "Pending"})
                    with open(reg_file, "w") as f:
                        json.dump(account_data, f, indent=4)
                    print(f"[SUCCESS] Na-save si {username} sa pending_accounts.json!")
        except Exception as e:
            print(f"[ERROR sa pag-save ng registration]: {e}")

    def process_log(self, data):
        try:
            parts = {p.split(": ")[0].strip(): p.split(": ")[1].strip() for p in data.split(" | ")}
            action, user, time_str = parts.get("ACTION"), parts.get("USER"), parts.get("TIME")
            if action == "LOGIN":
                self.all_logs.append({"user": user, "login": time_str, "logout": "--", "duration": "--"})
            elif action == "LOGOUT":
                for entry in reversed(self.all_logs):
                    if entry['user'] == user and entry['logout'] == "--":
                        login_dt = datetime.datetime.strptime(entry['login'], "%H:%M:%S")
                        logout_dt = datetime.datetime.strptime(time_str, "%H:%M:%S")
                        entry.update({"logout": time_str, "duration": str(logout_dt - login_dt)})
                        break
        except: pass

    # --- FULL SCREEN DEMO BROADCAST SERVER (Naka-optimize para sa Wi-Fi / Real-Time) ---
    def broadcast_stream_server(self):
        PORT = 9996
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(("0.0.0.0", PORT))
            server.listen(10)
            self.broadcast_socket = server
            print(f"[DEBUG] Broadcast Stream Server ay aktibo sa port {PORT}")
        except Exception as e:
            print(f"[ERROR sa Broadcast Server]: {e}")
            return
        
        while True:
            try:
                server.settimeout(1.0)
                conn, addr = server.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                threading.Thread(target=self.stream_handler, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except:
                break

    def stream_handler(self, conn):
        self.active_broadcast = True
        while self.active_broadcast:
            try:
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
                
                _, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
                data = encoded.tobytes()
                
                header = struct.pack("!I", len(data))
                conn.sendall(header + data)
                
                time.sleep(0.03)
            except:
                break
        try:
            conn.close()
        except:
            pass

    def check_login(self):
        username = self.user_entry.get()
        if username in self.USERS and self.USERS[username]["password"] == self.pass_entry.get():
            self.withdraw()
            role = self.USERS[username]["role"]
            if role == "Teacher": 
                dashboard = TeacherDashboard(master_app=self)
                self.active_teacher_dashboard = dashboard  # <--- I-save ang instance dito
            elif role == "Admin": 
                dashboard = AdminDashboard(master_app=self)
            dashboard.protocol("WM_DELETE_WINDOW", lambda: self.on_dashboard_close(dashboard))
        else: self.error_label.configure(text="Invalid credentials!", text_color="red")

    def on_dashboard_close(self, dashboard):
        if dashboard == self.active_teacher_dashboard:
            self.active_teacher_dashboard = None
        dashboard.destroy()
        self.deiconify()

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()