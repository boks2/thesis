import socket
import threading
import io
import json
import os
from datetime import datetime
from PIL import Image, ImageTk

LOG_PORT = 5001

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REG_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "pending_accounts.json"))

def start_log_listener(self):
    """Tatakbo sa sariling thread para mag-abang ng registrations, logins, at expressions sa Port 5001"""
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

            elif "ACTION: LOGIN" in command or "ACTION: LOGIN_CHECK" in command:
                parts = command.split("|")
                username = ""
                for part in parts:
                    if "USER:" in part:
                        username = part.split("USER:")[1].strip()
                
                if "ACTION: LOGIN_CHECK" in command:
                    try:
                        conn.sendall(b"SUCCESS")
                    except:
                        pass

                if username and hasattr(self, 'after'):
                    self.after(0, lambda u=username, ip=addr[0]: update_student_card_name(self, u, ip))
            
            elif "EXPRESSION:" in command:
                expr_content = command.replace("EXPRESSION:", "").strip()
                if hasattr(self, 'after'):
                    self.after(0, lambda e=expr_content: handle_student_expression(self, e, addr[0]))
            
            conn.close()
        except Exception as e:
            print(f"[ERROR sa Log Listener]: {e}")

def handle_student_expression(self, expression_text, sender_ip):
    """Nag-a-update ng expression sa card UI gamit ang IP address o PC match format"""
    print(f"[STUDENT EXPRESSION ALERT] mula {sender_ip}: {expression_text}")
    try:
        parts = expression_text.split("|")
        if len(parts) >= 2:
            expression = parts[1].strip()
        else:
            expression = expression_text.strip()
            
        target_card_info = None
        matched_key = None
        
        # 1. Subukang direktang hanapin gamit ang buong sender_ip bilang key
        if sender_ip in self.student_cards:
            matched_key = sender_ip
            target_card_info = self.student_cards[sender_ip]
        else:
            # 2. Hanapin sa bawat card kung nagtataglay ng IP o tugma ang PC suffix nito
            for key, card_info in self.student_cards.items():
                if sender_ip in key or (isinstance(card_info, dict) and sender_ip in str(card_info)):
                    matched_key = key
                    target_card_info = card_info
                    break
                
                # Hanapin ang tugma base sa dulo ng IP (hal. PC 40 mula sa 192.168.100.40)
                pc_suffix = f"PC {sender_ip.split('.')[-1]}"
                if isinstance(card_info, dict) and pc_suffix in card_info.get("name", ""):
                    matched_key = key
                    target_card_info = card_info
                    break

        if target_card_info:
            target_card_info["expression"] = expression
            
            current_name = target_card_info["name"]
            
            # Alisin ang dating nakalagay na expression para hindi magpatong-patong
            if " | [" in current_name:
                base_name = current_name.split(" | [")[0].strip()
            else:
                base_name = current_name.strip()
                
            # I-update ang pangalan na may kasamang expression format
            target_card_info["name"] = f"{base_name} | [{expression}]"
            
            if "info_label" in target_card_info and target_card_info["info_label"].winfo_exists():
                target_card_info["info_label"].configure(text=f"{target_card_info['name']} ({sender_ip})")
                print(f"[SUCCESS] Na-update ang card para sa IP {sender_ip} na may expression: {expression}")
        else:
            print(f"[WARNING] Walang nahanap na student card para sa IP: {sender_ip}")
            
    except Exception as e:
        print(f"[ERROR parsing expression]: {e}")

    if hasattr(self, 'show_notification'):
        self.show_notification(f"Expression: {expression_text}")

def update_student_card_name(self, username, ip):
    pc_label = f"PC {ip.split('.')[-1]}"
    display_name = f"{username} - {pc_label}"
    
    if ip not in self.student_cards or "frame" not in self.student_cards[ip] or not self.student_cards[ip]["frame"].winfo_exists():
        from .student_cards import create_student_card
        create_student_card(self, display_name, ip, len(self.student_cards))
    else:
        card_info = self.student_cards[ip]
        card_info["name"] = display_name
        if "info_label" in card_info and card_info["info_label"].winfo_exists():
            card_info["info_label"].configure(text=f"{display_name} ({ip})")
            
        if "preview" in card_info and card_info["preview"].winfo_exists():
            card_info["preview"].configure(text=f"{display_name}\n(Waiting for Live Stream...)")

def start_global_listener(self):
    threading.Thread(target=start_log_listener, args=(self,), daemon=True).start()

    def handle_client(conn, addr):
        student_ip = addr[0]
        self.connected_students[student_ip] = conn
        
        display_name = f"User - {student_ip}"
        
        try:
            conn.settimeout(3.0)
            raw_user_info = conn.recv(128).decode('utf-8', errors='ignore').strip()
            conn.settimeout(None)
            
            if "NAME:" in raw_user_info:
                parts = raw_user_info.split("NAME:")
                if len(parts) > 1:
                    actual_username = parts[1].split("\n")[0].strip()
                    if actual_username:
                        display_name = f"{actual_username} - PC {student_ip.split('.')[-1]}"
        except Exception as e:
            conn.settimeout(None)

        clean_username = display_name.split(" - ")[0]
        self.after(0, lambda u=clean_username, ip=student_ip: update_student_card_name(self, u, ip))
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
            
            def remove_card_ui():
                if student_ip in self.student_cards:
                    try:
                        card_info = self.student_cards[student_ip]
                        if isinstance(card_info, dict):
                            if "card" in card_info and card_info["card"].winfo_exists():
                                card_info["card"].destroy()
                            elif "frame" in card_info and card_info["frame"].winfo_exists():
                                card_info["frame"].destroy()
                        elif hasattr(card_info, "destroy"):
                            card_info.destroy()
                    except Exception as e:
                        print(f"Error sa pagbura ng card para sa {student_ip}: {e}")
                    del self.student_cards[student_ip]

            if hasattr(self, 'after'):
                self.after(0, remove_card_ui)
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

    def handle_remote_client(conn, addr):
        student_ip = addr[0]
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
                    img_tk = ImageTk.PhotoImage(image)
                    
                    if hasattr(self, 'active_viewers') and student_ip in self.active_viewers:
                        viewer = self.active_viewers[student_ip]
                        if viewer.winfo_exists():
                            viewer.after(0, lambda img=img_tk, v=viewer: v.update_image(img))
        except Exception as e:
            print(f"Remote view error for {student_ip}: {e}")
        finally:
            conn.close()

    def remote_listener():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 9997))
        server.listen(10)
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_remote_client, args=(conn, addr), daemon=True).start()

    threading.Thread(target=remote_listener, daemon=True).start()

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