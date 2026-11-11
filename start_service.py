import subprocess
import os
import sys
import re
import time
import socket

BASE_DIR = r"C:\Users\USER\Desktop\pointage_arex"
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

# Start app.py if needed
if not is_port_open(8080):
    print("[*] Démarrage de app.py sur le port 8080...")
    subprocess.Popen([sys.executable, "app.py", "8080"], cwd=BASE_DIR)
    time.sleep(2)
else:
    print("[OK] app.py est déjà actif sur le port 8080.")

print("[*] Lancement du tunnel Cloudflare...")
proc = subprocess.Popen(
    [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

found_url = None

while True:
    line = proc.stdout.readline()
    if not line:
        time.sleep(0.1)
        continue
    
    clean = line.strip()
    # Check for URL
    m = re.search(r"https://([a-zA-Z0-9\-]+)\.trycloudflare\.com", clean)
    if m and not found_url and m.group(1) != "api":
        found_url = m.group(0)
        url_scanner = f"{found_url}/scanner"
        url_admin = f"{found_url}/"

        print(f"\n=======================================================", flush=True)
        print(f"!!!URL_SUCCESS!!!{found_url}", flush=True)
        print(f"SCANNER: {url_scanner}", flush=True)
        print(f"ADMIN:   {url_admin}", flush=True)
        print(f"=======================================================\n", flush=True)

        with open(os.path.join(BASE_DIR, "current_url.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL={found_url}\nSCANNER={url_scanner}\nADMIN={url_admin}\n")

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
⚠️ NOTE IMPORTANTE :
Ces liens sont immédiatement actifs et accessibles partout dans le monde.
====================================================================
""")
    if "Registered tunnel" in clean:
        print("[*] Connexion tunnel Cloudflare confirmée active.", flush=True)
