import customtkinter as ctk
import json
import os

# Gamitin ang absolute path patungo sa root folder para pareho sila ng pinaglalagyan
# Sa loob ng teacher_dashboard/account_approvals.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Siguraduhing dalawang tuldok (..) ang gamit para umakyat sa root folder:
USER_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "users.json"))
REQUEST_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "pending_accounts.json"))
def open_account_approvals(master_teacher):
    window = ctk.CTkToplevel(master_teacher)
    window.title("Account Approvals Management")
    window.geometry("750x550")
    window.attributes("-topmost", True)
    
    ctk.CTkLabel(window, text="Student Account Requests", font=("Arial", 18, "bold")).pack(pady=15)
    
    # Tabview para sa Pending, Accepted, at Declinedss
    tabview = ctk.CTkTabview(window, width=700, height=380)
    tabview.pack(padx=20, pady=5)
    
    tab_pending = tabview.add("Pending")
    tab_accepted = tabview.add("Accepted")
    tab_declined = tabview.add("Declined")
    
    def load_data():
        for widget in tab_pending.winfo_children(): widget.destroy()
        for widget in tab_accepted.winfo_children(): widget.destroy()
        for widget in tab_declined.winfo_children(): widget.destroy()
        
        if not os.path.exists(REQUEST_FILE):
            with open(REQUEST_FILE, "w") as f:
                json.dump([], f)
                
        with open(REQUEST_FILE, "r") as f:
            try:
                accounts = json.load(f)
            except:
                accounts = []
            
        for acc in accounts:
            username = acc["username"]
            status = acc.get("status", "Pending")
            
            if status == "Pending":
                frm = ctk.CTkFrame(tab_pending)
                frm.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(frm, text=f"Username: {username}", font=("Arial", 12)).pack(side="left", padx=10)
                
                ctk.CTkButton(frm, text="Decline", fg_color="red", width=80, 
                              command=lambda u=username: update_status(u, "Declined")).pack(side="right", padx=5)
                ctk.CTkButton(frm, text="Accept", fg_color="green", width=80, 
                              command=lambda u=username: update_status(u, "Accepted")).pack(side="right", padx=5)
                              
            elif status == "Accepted":
                frm = ctk.CTkFrame(tab_accepted)
                frm.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(frm, text=f"Username: {username} (Approved)", text_color="green", font=("Arial", 12)).pack(side="left", padx=10)
                
            elif status == "Declined":
                frm = ctk.CTkFrame(tab_declined)
                frm.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(frm, text=f"Username: {username} (Rejected)", text_color="red", font=("Arial", 12)).pack(side="left", padx=10)

    def update_status(username, new_status):
        if not os.path.exists(REQUEST_FILE):
            return
            
        with open(REQUEST_FILE, "r") as f:
            try:
                accounts = json.load(f)
            except:
                accounts = []
            
        target_account = None
        for acc in accounts:
            if acc["username"] == username:
                acc["status"] = new_status
                target_account = acc
                
        with open(REQUEST_FILE, "w") as f:
            json.dump(accounts, f, indent=4)
            
        # Kapag in-accept, otomatikong maidaragdag sa users.json para makapag-login ang estudyante
        if new_status == "Accepted" and target_account:
            users_data = {}
            if os.path.exists(USER_FILE):
                with open(USER_FILE, "r") as f:
                    try: 
                        users_data = json.load(f)
                    except: 
                        users_data = {}
            
            users_data[username] = {"password": target_account["password"], "role": "Student"}
            with open(USER_FILE, "w") as f:
                json.dump(users_data, f, indent=4)
                
        load_data()

    # Button para i-refresh ang listahan ng mga nagrerehistro[cite: 1, 2]
    ctk.CTkButton(window, text="Refresh List", fg_color="#1f6aa5", command=load_data).pack(pady=10)

    load_data()