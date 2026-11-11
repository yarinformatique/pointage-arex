import subprocess
import os
import sys
import re
import time

BASE_DIR = r"C:\Users\USER\Desktop\pointage_arex"
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")

proc = subprocess.Popen(
    [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

found_url = None
start = time.time()
while time.time() - start < 30:
    line = proc.stdout.readline()
    if line:
        line_str = line.strip()
        if "trycloudflare.com" in line_str and "api.trycloudflare.com" not in line_str:
            parts = line_str.split("https://")
            if len(parts) > 1:
                url_part = "https://" + parts[1].split()[0].strip("|").strip()
                if ".trycloudflare.com" in url_part:
                    found_url = url_part
                    break
    time.sleep(0.05)

if found_url:
    url_scanner = f"{found_url}/scanner"
    url_admin = f"{found_url}/"
    with open(os.path.join(BASE_DIR, "final_url.txt"), "w", encoding="utf-8") as f:
        f.write(f"SCANNER={url_scanner}\nADMIN={url_admin}\n")
    with open(os.path.join(DESKTOP_DIR, "LIEN_POINTAGE_AREX.txt"), "w", encoding="utf-8") as f:
        f.write(f"SCANNER: {url_scanner}\nADMIN: {url_admin}\n")
    print("SUCCESS_URL:", found_url, flush=True)

# Don't terminate, keep tunnel running!
while True:
    time.sleep(10)
