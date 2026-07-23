# network_utils.py
import socket

def send_command(target_student_ip, command):
    """Para sa LOCK/UNLOCK (Port 5000)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2) 
            s.connect((target_student_ip, 5000))
            s.sendall(command.encode()) # Tinanggal ang \n para tumugma sa student[cite: 5]
            print(f"Command '{command}' sent to {target_student_ip}")
    except Exception as e:
        print(f"Hindi makakonekta sa student PC {target_student_ip}: {e}")

def send_control_command(target_ip, command):
    """Para sa Control Commands (Port 9999)[cite: 5]"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((target_ip, 9999))
            s.sendall(f"{command}\n".encode())
            print(f"Control command '{command}' sent to {target_ip}")
    except Exception as e:
        print(f"Control command error: {e}")