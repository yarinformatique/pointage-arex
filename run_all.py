import subprocess
import os
import sys
import time
import socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

BASE_DIR = r"C:\Users\USER\Desktop\pointage_arex"

if not is_port_open(8080):
    subprocess.Popen([sys.executable, "app.py", "8080"], cwd=BASE_DIR)
    time.sleep(1.5)

# Run get_tunnel_url.py
subprocess.run([sys.executable, "get_tunnel_url.py"], cwd=BASE_DIR)
