import customtkinter as ctk
import json
import os
import socket
import threading
import datetime
from config import apply_theme
from teacher_dashboard.teacher_dash import TeacherDashboard
from admin_dashboard.admin_dash import AdminDashboard

apply_theme()

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScholarNet Login")
        self.geometry("350x400")
        
        self.USERS = {
            "student": {"password": "student123", "role": "Student"},
            "teacher": {"password": "teacher123", "role": "Teacher"},
            "admin": {"password": "admin123", "role": "Admin"}
        }
        
        self.all_logs = [] 
        threading.Thread(target=self.start_log_listener, daemon=True).start()
        
        ctk.CTkLabel(self, text="ScholarNet Login", font=("Arial", 20)).pack(pady=20)
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
        while True:
            try:
                conn, addr = server.accept()
                data = conn.recv(1024).decode()
                self.process_log(data)
                conn.close()
            except: break

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

    def check_login(self):
        username = self.user_entry.get()
        if username in self.USERS and self.USERS[username]["password"] == self.pass_entry.get():
            self.withdraw()
            role = self.USERS[username]["role"]
            if role == "Teacher": dashboard = TeacherDashboard(master_app=self)
            elif role == "Admin": dashboard = AdminDashboard(master_app=self)
            dashboard.protocol("WM_DELETE_WINDOW", lambda: self.on_dashboard_close(dashboard))
        else: self.error_label.configure(text="Invalid credentials!", text_color="red")

    def on_dashboard_close(self, dashboard):
        dashboard.destroy()
        self.deiconify()

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()