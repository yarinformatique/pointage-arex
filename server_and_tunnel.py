import subprocess
import os
import sys
import time
import socket
import re

BASE_DIR = r"C:\Users\USER\Desktop\pointage_arex"
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

# Start server if not running
if not is_port_open(8080):
    server_p = subprocess.Popen([sys.executable, "app.py", "8080"], cwd=BASE_DIR)
    time.sleep(2)

# Start cloudflared
cf_proc = subprocess.Popen([CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, encoding="utf-8", errors="replace")

found_url = None
t0 = time.time()
while time.time() - t0 < 30:
    line = cf_proc.stderr.readline()
    if not line:
        continue
    if "trycloudflare.com" in line:
        m = re.search(r"https://([a-zA-Z0-9-]+)\.trycloudflare\.com", line)
        if m and m.group(1) != "api":
            found_url = m.group(0)
            break

if found_url:
    print(f"!!!URL_SUCCESS!!!{found_url}", flush=True)
    with open(os.path.join(BASE_DIR, "current_url.txt"), "w", encoding="utf-8") as f:
        f.write(found_url)
    with open(r"C:\Users\USER\Desktop\LIEN_POINTAGE_AREX.txt", "w", encoding="utf-8") as f:
        f.write(f"""====================================================================
   POINTAGE AREX - LIENS OFFICIELS EN LIGNE (4G / WI-FI)
   Chantier & Direction - Bobo-Dioulasso, Burkina Faso
====================================================================

📱 1. LIEN DU PROMOTEUR SUR SMARTPHONE (APPLICATION SCANNER PURE) :
   👉 {found_url}/scanner

--------------------------------------------------------------------

💻 2. LIEN DIRECTION / RH (TABLEAU DE BORD COMPLET & EXCEL) :
   👉 {found_url}/

====================================================================
""")
else:
    print("!!!URL_FAILED!!!", flush=True)

# Keep process alive
cf_proc.wait()
