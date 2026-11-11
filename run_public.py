import subprocess
import sys
import os
import re
import time
import socket
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

# 1. Start App server in background thread or process
if not is_port_open(8080):
    print("[*] Lancement du serveur Python app.py sur le port 8080...")
    server_proc = subprocess.Popen([sys.executable, "app.py", "8080"], cwd=BASE_DIR)
    time.sleep(2)
else:
    print("[OK] Serveur déjà actif sur le port 8080.")

# 2. Launch cloudflared tunnel
print("[*] Connexion au réseau Cloudflare...")
cmd = [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"]
tunnel_proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    encoding="utf-8",
    errors="replace"
)

public_url = None

def monitor_stream(stream):
    global public_url
    for line in iter(stream.readline, ""):
        # Match trycloudflare URL (excluding api.trycloudflare.com)
        m = re.search(r"https://([a-zA-Z0-9-]+)\.trycloudflare\.com", line)
        if m and m.group(1) != "api" and not public_url:
            public_url = m.group(0)
            url_scanner = f"{public_url}/scanner"
            url_admin = f"{public_url}/"

            print(f"\n====================================================================")
            print(f"URL_PUBLIQUE_SCANNER: {url_scanner}")
            print(f"URL_PUBLIQUE_ADMIN:   {url_admin}")
            print(f"====================================================================\n", flush=True)

            # Write to files
            with open(os.path.join(BASE_DIR, "current_url.txt"), "w", encoding="utf-8") as f:
                f.write(f"SCANNER={url_scanner}\nADMIN={url_admin}\n")

            content = f"""====================================================================
   POINTAGE AREX - LIENS OFFICIELS EN LIGNE (4G / WI-FI)
   Chantier & Direction - Bobo-Dioulasso, Burkina Faso
====================================================================

📱 1. LIEN DU PROMOTEUR SUR SMARTPHONE (APPLICATION SCANNER PURE) :
   👉 {url_scanner}

   (Ce lien ouvre directement la caméra plein écran pour scanner les ouvriers)

--------------------------------------------------------------------

💻 2. LIEN DIRECTION / RH (TABLEAU DE BORD COMPLET & EXCEL) :
   👉 {url_admin}

   (Consultez les arrivées, retards, anomalies, et téléchargez Excel)

====================================================================
"""
            with open(os.path.join(DESKTOP_DIR, "LIEN_POINTAGE_AREX.txt"), "w", encoding="utf-8") as f:
                f.write(content)

t1 = threading.Thread(target=monitor_stream, args=(tunnel_proc.stderr,), daemon=True)
t2 = threading.Thread(target=monitor_stream, args=(tunnel_proc.stdout,), daemon=True)
t1.start()
t2.start()

# Wait for URL to appear
for _ in range(30):
    if public_url:
        break
    time.sleep(1)

# Keep process alive
try:
    tunnel_proc.wait()
except KeyboardInterrupt:
    tunnel_proc.terminate()
