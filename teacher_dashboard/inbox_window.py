import customtkinter as ctk

def open_inbox_window(master_dashboard):
    # Siguraduhing walang naiwang lumang inbox window para maiwasan ang conflict
    if hasattr(master_dashboard, 'current_inbox_win') and master_dashboard.current_inbox_win:
        try:
            master_dashboard.current_inbox_win.destroy()
        except:
            pass

    inbox_win = ctk.CTkToplevel(master_dashboard)
    master_dashboard.current_inbox_win = inbox_win  # I-save ang reference para sa real-time refresh
    
    inbox_win.title("Teacher's Student Activity Inbox")
    inbox_win.geometry("600x400")
    
    ctk.CTkLabel(inbox_win, text="Real-time Student Activity Inbox", font=("Arial", 16, "bold")).pack(pady=10)
    
    # Frame para sa listahan ng mga logs
    frame = ctk.CTkScrollableFrame(inbox_win, width=550, height=300)
    frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Debug print para makita sa terminal ang laman ng data kapag binuksan
    print(f"[DEBUG INBOX WINDOW] Kasalukuyang laman ng inbox_logs_data: {getattr(master_dashboard, 'inbox_logs_data', [])}")
    
    if not hasattr(master_dashboard, 'inbox_logs_data') or not master_dashboard.inbox_logs_data:
        ctk.CTkLabel(frame, text="Wala pang natatanggap na aktibidad mula sa mga estudyante.", text_color="gray").pack(pady=20)
    else:
        for log in reversed(master_dashboard.inbox_logs_data):
            log_text = f"[{log.get('time', '')}] {log.get('message', '')}"
            lbl = ctk.CTkLabel(frame, text=log_text, anchor="w", justify="left", font=("Arial", 12))
            lbl.pack(fill="x", padx=5, pady=2)
            
    # Button para mag-clear ng inbox
    def clear_inbox():
        if hasattr(master_dashboard, 'inbox_logs_data'):
            master_dashboard.inbox_logs_data.clear()
        master_dashboard.current_inbox_win = None
        inbox_win.destroy()
        open_inbox_window(master_dashboard)

    # Linisin ang reference kapag pinindot ang 'X' (close) ng window
    def on_close():
        master_dashboard.current_inbox_win = None
        inbox_win.destroy()

    inbox_win.protocol("WM_DELETE_WINDOW", on_close)

    ctk.CTkButton(inbox_win, text="Clear Inbox", fg_color="#d9534f", hover_color="#c9302c", command=clear_inbox).pack(pady=10)