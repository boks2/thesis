import customtkinter as ctk

def setup_grid_layout(self):
    self.grid_frame = ctk.CTkScrollableFrame(self, label_text="Lab Monitoring Grid", height=400)
    self.grid_frame.pack(fill="both", expand=True, padx=20, pady=10)
    self.grid_frame.grid_columnconfigure((0, 1, 2), weight=1)
   
    # Tinanggal na natin ang hardcoded na "Waiting for Student..." 
    # para magsimula nang malinis ang grid at lumitaw lamang ang card kapag may nag-login o nag-stream.

def create_student_card(self, name, ip, index):
    if ip in self.student_cards:
        return

    row = index // 3
    col = index % 3

    pc_card = ctk.CTkFrame(self.grid_frame, fg_color="#2b2b2b", corner_radius=6)
    pc_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    screen_preview = ctk.CTkFrame(pc_card, height=160, fg_color="#1a1a1a", corner_radius=4)
    screen_preview.pack(fill="x", padx=8, pady=8)
    screen_preview.pack_propagate(False)
   
    lbl_preview = ctk.CTkLabel(screen_preview, text=f"{name}\n(Waiting for Live Stream...)", text_color="#aaaaaa", font=ctk.CTkFont(size=11))
    lbl_preview.pack(fill="both", expand=True)
   
    lbl_preview.bind("<Button-3>", lambda e: self.show_context_menu(e, ip, name))
    screen_preview.bind("<Button-3>", lambda e: self.show_context_menu(e, ip, name))

    lbl_info_text = ctk.CTkLabel(pc_card, text=f"{name} ({ip})", font=ctk.CTkFont(size=12, weight="bold"), text_color="white")
    lbl_info_text.pack(pady=(0, 8))
    lbl_info_text.bind("<Button-3>", lambda e: self.show_context_menu(e, ip, name))

    self.student_cards[ip] = {
        "card": pc_card,
        "preview": lbl_preview,
        "info_label": lbl_info_text,
        "name": name
    }