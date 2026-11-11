import subprocess
import time

CLOUDFLARED = r"C:\Users\USER\Desktop\pointage_arex\cloudflared.exe"
proc = subprocess.Popen([CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

with open(r"C:\Users\USER\Desktop\pointage_arex\cf_full_output.txt", "w", encoding="utf-8") as f:
    start = time.time()
    while time.time() - start < 20:
        line = proc.stdout.readline()
        if line:
            f.write(line)
            f.flush()
        else:
            time.sleep(0.1)

proc.terminate()
