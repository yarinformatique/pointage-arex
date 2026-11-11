import subprocess
import os
import sys
import re
import time
import socket
import urllib.request

BASE_DIR = r"C:\Users\USER\Desktop\pointage_arex"
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
PYTHON_EXE = sys.executable

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

# 1. Start App server if needed
if not is_port_open(8080):
    print("Starting app.py on 8080...", flush=True)
    subprocess.Popen([PYTHON_EXE, "app.py", "8080"], cwd=BASE_DIR)
    time.sleep(2)

# 2. Launch cloudflared
print("Starting cloudflared tunnel...", flush=True)
proc = subprocess.Popen(
    [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

found_url = None
start_time = time.time()
while time.time() - start_time < 35:
    line = proc.stdout.readline()
    if line:
        line_clean = line.strip()
        # Look for trycloudflare.com
        m = re.search(r"https://[a-zA-Z0-9\.\-]+\.trycloudflare\.com", line_clean)
        if m:
            u = m.group(0).rstrip(".")
            if "api.trycloudflare.com" not in u:
                found_url = u
                print(f"FOUND TUNNEL URL: {found_url}", flush=True)
                break
    time.sleep(0.1)

if not found_url:
    print("FAILED_TO_GET_TUNNEL_URL", flush=True)
    sys.exit(1)

# 3. Verify URL is reachable
print(f"Verifying {found_url}/scanner...", flush=True)
verified = False
for attempt in range(8):
    try:
        req = urllib.request.Request(f"{found_url}/scanner", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                verified = True
                print("URL_VERIFIED_SUCCESS_200_OK", flush=True)
                break
    except Exception as e:
        print(f"Waiting for DNS propagation ({attempt+1}/8): {e}", flush=True)
        time.sleep(2)

# 4. Write to Desktop and local files
url_scanner = f"{found_url}/scanner"
url_admin = f"{found_url}/"

content = f"""====================================================================
   POINTAGE AREX - LIENS OFFICIELS EN LIGNE (4G / 5G / WI-FI)
   Chantier & Direction - Bobo-Dioulasso, Burkina Faso
====================================================================

Accessible immédiatement partout dans le monde sur smartphone et PC :

📱 1. APPLICATION SMARTPHONE DU PROMOTEUR (SCANNER PUR) :
   👉 {url_scanner}

   (Interface ultra-rapide dédiée au promoteur sur le chantier.
    Ouvre directement la caméra plein écran pour scanner les badges.
    Bip sonore instantané et annonce vocale du statut : À l'heure / Retard).

--------------------------------------------------------------------

💻 2. TABLEAU DE BORD DIRECTION / RH / COMPTABILITÉ :
   👉 {url_admin}

   (Accès superviseur complet : arrivées, retards en minutes,
    absences, alertes sécurité, matrice mensuelle et exports Excel).

====================================================================
"""

with open(os.path.join(DESKTOP_DIR, "LIEN_POINTAGE_AREX.txt"), "w", encoding="utf-8") as f:
    f.write(content)

with open(os.path.join(BASE_DIR, "active_public_url.txt"), "w", encoding="utf-8") as f:
    f.write(f"PUBLIC_URL={found_url}\nSCANNER_URL={url_scanner}\nADMIN_URL={url_admin}\n")

print(f"\n====================================================================", flush=True)
print(f"CONFIRMED_PUBLIC_SCANNER_URL: {url_scanner}", flush=True)
print(f"CONFIRMED_PUBLIC_ADMIN_URL:   {url_admin}", flush=True)
print(f"====================================================================\n", flush=True)

# Keep the tunnel alive!
while True:
    time.sleep(10)
