import subprocess
import time

CLOUDFLARED = r"C:\Users\USER\Desktop\pointage_arex\cloudflared.exe"
log_file = r"C:\Users\USER\Desktop\pointage_arex\cf_http2.log"

with open(log_file, "w", encoding="utf-8") as out:
    p = subprocess.Popen([CLOUDFLARED, "tunnel", "--protocol", "http2", "--url", "http://127.0.0.1:8080"], stderr=out, stdout=out)
    time.sleep(15)
    p.terminate()

with open(log_file, "r", encoding="utf-8", errors="replace") as f:
    print(f.read())
