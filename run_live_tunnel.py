import subprocess
import time
import os
import sys
import socket

BASE_DIR = r"C:\Users\USER\Desktop\pointage_arex"
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

# Start app.py if not already running
if not is_port_open(8080):
    subprocess.Popen([sys.executable, "app.py", "8080"], cwd=BASE_DIR)
    time.sleep(2)

proc = subprocess.Popen(
    [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

found_url = None
t0 = time.time()

with open(os.path.join(BASE_DIR, "tunnel_session.log"), "w", encoding="utf-8") as log:
    while time.time() - t0 < 35:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        log.write(line)
        log.flush()
        
        # Detect URL line
        if "trycloudflare.com" in line and "api.trycloudflare.com" not in line:
            for part in line.split():
                if "trycloudflare.com" in part and part.startswith("https://"):
                    found_url = part.strip("|").strip()
                    break
        if found_url:
            break

if found_url:
    url_scanner = f"{found_url}/scanner"
    url_admin = f"{found_url}/"

    with open(os.path.join(BASE_DIR, "current_url.txt"), "w", encoding="utf-8") as f:
        f.write(f"SCANNER={url_scanner}\nADMIN={url_admin}\n")

    with open(os.path.join(DESKTOP_DIR, "LIEN_POINTAGE_AREX.txt"), "w", encoding="utf-8") as f:
        f.write(f"""====================================================================
   POINTAGE AREX - LIENS OFFICIELS EN LIGNE (4G / WI-FI)
   Chantier & Direction - Bobo-Dioulasso, Burkina Faso
====================================================================

📱 1. LIEN DU PROMOTEUR SUR SMARTPHONE (APPLICATION SCANNER PURE) :
   👉 {url_scanner}

   (Sur smartphone, ce lien ouvre directement la caméra plein écran 
    avec bip sonore, validation vocale et grand badge du statut !)

--------------------------------------------------------------------

💻 2. LIEN DIRECTION / RH (TABLEAU DE BORD COMPLET & EXCEL) :
   👉 {url_admin}

   (Consultez les arrivées, retards, anomalies, et téléchargez Excel)

====================================================================
""")
    print("LIVE_SUCCESS:" + found_url, flush=True)
else:
    print("LIVE_FAILED", flush=True)

# Keep running
while True:
    line = proc.stdout.readline()
    if not line:
        time.sleep(1)
