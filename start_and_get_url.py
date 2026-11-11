import subprocess
import os
import sys
import re
import time

CLOUDFLARED = r"C:\Users\USER\Desktop\pointage_arex\cloudflared.exe"
proc = subprocess.Popen([CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, encoding="utf-8", errors="replace")

found_url = None
start = time.time()
while time.time() - start < 25:
    line = proc.stderr.readline()
    if not line:
        continue
    # print line for log
    if "trycloudflare.com" in line:
        m = re.search(r"https://([a-zA-Z0-9-]+)\.trycloudflare\.com", line)
        if m and m.group(1) != "api":
            found_url = m.group(0)
            break

if found_url:
    print(f"FOUND_URL:{found_url}", flush=True)
    with open(r"C:\Users\USER\Desktop\pointage_arex\current_url.txt", "w", encoding="utf-8") as f:
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
    print("FAILED_TO_FIND_URL", flush=True)

# Keep running
try:
    proc.wait()
except Exception:
    proc.terminate()
