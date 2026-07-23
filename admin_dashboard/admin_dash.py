import customtkinter as ctk
import tkinter.ttk as ttk
import socket  # Inilipat sa itaas (Standard practice)

class AdminDashboard(ctk.CTkToplevel):
    def __init__(self, master_app):
        super().__init__()
        self.master_app = master_app
        self.title("Super Admin Dashboard")
        self.geometry("900x600")
        
        tabview = ctk.CTkTabview(self)
        tabview.pack(expand=True, fill="both", padx=20, pady=20)
        
        tabview.add("Logs & History")
        tabview.add("User Management")
        
        # --- Logs & History Tab ---
        self.search_entry = ctk.CTkEntry(tabview.tab("Logs & History"), placeholder_text="Search student name...")
        self.search_entry.pack(pady=10, fill="x")
        self.search_entry.bind("<KeyRelease>", self.filter_logs)
        
        self.tree = ttk.Treeview(tabview.tab("Logs & History"), columns=("User", "Login", "Logout", "Duration"), show='headings')
        for col in ["User", "Login", "Logout", "Duration"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True)
        
        # --- User Management Tab ---
        ctk.CTkLabel(tabview.tab("User Management"), text="Reset Student Password", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.target_user_entry = ctk.CTkEntry(tabview.tab("User Management"), placeholder_text="Enter Student Username")
        self.target_user_entry.pack(pady=10)
        
        ctk.CTkButton(tabview.tab("User Management"), text="Reset to 'student123'", 
                      fg_color="red", command=self.reset_student_password).pack(pady=10)
        
        self.status_label = ctk.CTkLabel(tabview.tab("User Management"), text="")
        self.status_label.pack()
        
        self.refresh_table()

    def reset_student_password(self):
        username = self.target_user_entry.get()
        if username in self.master_app.USERS:
            self.master_app.USERS[username]["password"] = "student123"
            self.master_app.save_users()
            
            try:
                STUDENT_PC_IP = "192.168.100.251"
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(5) # Maghintay ng 5 segundo
                client.connect((STUDENT_PC_IP, 5000))
                client.send("RESET_PWD".encode())
                client.close()
                self.status_label.configure(text="Reset success!", text_color="green")
            except Exception as e:
                # DITO NATIN MAKIKITA ANG TUNAY NA DAHILAN
                self.status_label.configure(text=f"Error: {str(e)}", text_color="red")
        else:
            self.status_label.configure(text="User not found!", text_color="red")
    def refresh_table(self, data=None):
        for item in self.tree.get_children(): self.tree.delete(item)
        target = data if data is not None else self.master_app.all_logs
        for entry in target:
            self.tree.insert("", "end", values=(entry['user'], entry['login'], entry['logout'], entry['duration']))

    def filter_logs(self, event):
        query = self.search_entry.get().lower()
        filtered = [log for log in self.master_app.all_logs if query in log['user'].lower()]
        self.refresh_table(filtered)