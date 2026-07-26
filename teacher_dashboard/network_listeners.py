import socket
import threading
import io
import json
import os
from datetime import datetime
from PIL import Image, ImageTk

LOG_PORT = 5001

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Direktang i-target ang root kung saan katabi ng login.py ang pending_accounts.json
REG_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "pending_accounts.json"))

def start_log_listener(self):
    """Tatakbo sa sariling thread para mag-abang ng registrations at logins sa Port 5001"""
    log_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    log_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        log_server.bind(("0.0.0.0", LOG_PORT))
        log_server.listen(10)
        print(f"\n==========================================")
        print(f"[DEBUG] Log listener ay BUKAS at ACTIVE sa port {LOG_PORT}")
        print(f"==========================================\n")
    except Exception as e:
        print(f"[ERROR] Hindi ma-bind ang Port {LOG_PORT}: {e}")
        return

    while True:
        try:
            conn, addr = log_server.accept()
            command = conn.recv(1024).decode().strip()
            print(f"[DEBUG] May pumasok mula sa {addr[0]}: '{command}'")
            
            if "ACTION: REGISTER" in command:
                parts = command.split("|")
                username = ""
                password = ""
                
                for part in parts:
                    if "USER:" in part:
                        username = part.split("USER:")[1].strip()
                    elif "PWD:" in part:
                        password = part.split("PWD:")[1].strip()
                
                if username and password:
                    data = []
                    if os.path.exists(REG_FILE):
                        with open(REG_FILE, "r") as f:
                            try: data = json.load(f)
                            except: data = []
                            
                    if not any(acc["username"] == username for acc in data):
                        data.append({"username": username, "password": password, "status": "Pending"})
                        with open(REG_FILE, "w") as f:
                            json.dump(data, f, indent=4)
                        print(f"[SUCCESS] Na-save si {username} sa pending_accounts.json!")

            # Sinasalo na nito pareho ang LOGIN at LOGIN_CHECK galing sa student app
            elif "ACTION: LOGIN" in command or "ACTION: LOGIN_CHECK" in command:
                parts = command.split("|")
                username = ""
                for part in parts:
                    if "USER:" in part:
                        username = part.split("USER:")[1].strip()
                
                # Kung LOGIN_CHECK ang dumating, mag-reply muna ng "SUCCESS" pabalik sa student para tuloy-tuloy ang pag-login nila
                if "ACTION: LOGIN_CHECK" in command:
                    try:
                        conn.sendall(b"SUCCESS")
                    except:
                        pass

                if username and hasattr(self, 'after'):
                    self.after(0, lambda u=username, ip=addr[0]: update_student_card_name(self, u, ip))
            
            conn.close()
        except Exception as e:
            print(f"[ERROR sa Log Listener]: {e}")

def update_student_card_name(self, username, ip):
    pc_label = f"PC {ip.split('.')[-1]}"
    display_name = f"{username} - {pc_label}"
    
    # I-update o i-store ang pangalan sa dictionary agad
    if ip not in self.student_cards:
        from .student_cards import create_student_card
        index = len(self.student_cards)
        # Direktang gawin ang card gamit ang tamang username at IP
        create_student_card(self, display_name, ip, index)
    else:
        # Kung nag-e-exist na, i-update ang text ng label nito
        card_info = self.student_cards[ip]
        card_info["name"] = display_name
        if "info_label" in card_info:
            card_info["info_label"].configure(text=f"{display_name} ({ip})")
            
        if "preview" in card_info:
            card_info["preview"].configure(text=f"{display_name}\n(Waiting for Live Stream...)")

def start_global_listener(self):
    # 1. Simulan agad ang Log Listener sa Port 5001
    threading.Thread(target=start_log_listener, args=(self,), daemon=True).start()

    # 2. Listener para sa Screen Streaming (Port 9998)
    def handle_client(conn, addr):
        student_ip = addr[0]
        self.connected_students[student_ip] = conn
        
        display_name = f"User - {student_ip}"
        
        # Subukang basahin ang pangalan nang may maikling timeout para hindi ma-block ang stream
        try:
            conn.settimeout(1.5)
            raw_user_info = conn.recv(64).decode('utf-8', errors='ignore').strip()
            conn.settimeout(None)
            
            if raw_user_info.startswith("NAME:"):
                actual_username = raw_user_info.split("NAME:")[1].strip()
                display_name = f"{actual_username} - PC {student_ip.split('.')[-1]}"
            
            # Kung mayroon na sa student_cards mula sa login (Port 5001), gamitin iyon
            if student_ip in self.student_cards and "name" in self.student_cards[student_ip]:
                display_name = self.student_cards[student_ip]["name"]
        except Exception:
            conn.settimeout(None)
            if student_ip in self.student_cards:
                display_name = self.student_cards[student_ip].get("name", f"User - {student_ip}")

        # Siguraduhing gagawa o iu-update ang card sa UI
        self.after(0, lambda: update_student_card_name(self, display_name.split(" - ")[0], student_ip))
        self.after(0, lambda: record_login(self, display_name, student_ip))
       
        try:
            while True:
                raw_length = conn.recv(4)
                if not raw_length: break
                frame_length = int.from_bytes(raw_length, byteorder='big')
               
                frame_data = b""
                while len(frame_data) < frame_length:
                    packet = conn.recv(frame_length - len(frame_data))
                    if not packet: break
                    frame_data += packet
                   
                if len(frame_data) == frame_length:
                    image = Image.open(io.BytesIO(frame_data))
                    image = image.resize((240, 150), Image.Resampling.LANCZOS)
                    img_tk = ImageTk.PhotoImage(image)
                    self.after(0, lambda ip=student_ip, img=img_tk: update_thumbnail_frame(self, ip, img))
        except Exception as e:
            print(f"Stream error with {student_ip}: {e}")
        finally:
            conn.close()
            if student_ip in self.connected_students:
                del self.connected_students[student_ip]
            self.after(0, lambda: record_logout(self, student_ip))
    def stream_listener():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 9998))
        server.listen(10)
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
           
    threading.Thread(target=stream_listener, daemon=True).start()


def update_thumbnail_frame(self, ip, img_tk):
    if ip in self.student_cards:
        lbl = self.student_cards[ip]["preview"]
        lbl.configure(image=img_tk, text="")
        lbl.image = img_tk

def record_login(self, name, ip):
    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in self.login_history_data:
        if item["ip"] == ip and item["logout"] == "Active / Online":
            return
    self.login_history_data.append({
        "name": name, "ip": ip, "login": login_time, "logout": "Active / Online", "duration": "-"
    })

def record_logout(self, ip):
    logout_time = datetime.now()
    logout_str = logout_time.strftime("%Y-%m-%d %H:%M:%S")
    for item in self.login_history_data:
        if item["ip"] == ip and item["logout"] == "Active / Online":
            item["logout"] = logout_str
            login_dt = datetime.strptime(item["login"], "%Y-%m-%d %H:%M:%S")
            duration_sec = int((logout_time - login_dt).total_seconds())
            hours, remainder = divmod(duration_sec, 3600)
            minutes, seconds = divmod(remainder, 60)
            item["duration"] = f"{hours}h {minutes}m {seconds}s"
            break