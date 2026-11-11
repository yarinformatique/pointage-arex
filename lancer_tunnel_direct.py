import subprocess
import os
import sys
import re
import time
import socket
import threading

BASE_DIR = r"C:\Users\USER\Desktop\pointage_arex"
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

# Start app.py if needed
if not is_port_open(8080):
    print("[*] Demarrage du serveur Pointage Arex sur le port 8080...", flush=True)
    subprocess.Popen([sys.executable, "app.py", "8080"], cwd=BASE_DIR)
    time.sleep(2)

print("[*] Connexion au reseau Cloudflare mondial (protocole QUIC)...", flush=True)
cmd = [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"]

proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

current_url = None

def stdout_reader():
    global current_url
    for line in proc.stdout:
        clean_line = line.strip()
        match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", clean_line)
        if match and not current_url and "api.trycloudflare.com" not in match.group(0):
            current_url = match.group(0)
            url_scanner = f"{current_url}/scanner"
            url_admin = f"{current_url}/"

            print("\n" + "=" * 68, flush=True)
            print("   >>> POINTAGE AREX EN LIGNE SUR LE RESEAU MONDIAL CLOUDFLARE <<<", flush=True)
            print("=" * 68, flush=True)
            print(f"\n[+] LIEN SCANNER SMARTPHONE (PROMOTEUR CHANTIER) :\n    {url_scanner}\n", flush=True)
            print(f"[+] LIEN DIRECTION / RH (TABLEAU DE BORD & EXCEL) :\n    {url_admin}\n", flush=True)
            print("=" * 68, flush=True)

            with open(os.path.join(BASE_DIR, "current_url.txt"), "w", encoding="utf-8") as f:
                f.write(f"SCANNER={url_scanner}\nADMIN={url_admin}\n")

            with open(os.path.join(DESKTOP_DIR, "LIEN_POINTAGE_AREX.txt"), "w", encoding="utf-8") as f:
                f.write(f"""====================================================================
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
""")

reader_thread = threading.Thread(target=stdout_reader, daemon=True)
reader_thread.start()

# Wait until URL is found
for _ in range(40):
    if current_url:
        break
    time.sleep(1)

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
