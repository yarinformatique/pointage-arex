import subprocess
import os

CLOUDFLARED = r"C:\Users\USER\Desktop\pointage_arex\cloudflared.exe"
proc = subprocess.run([CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8080"], capture_output=True, text=True, timeout=12)
print("STDOUT:", proc.stdout[:500])
print("STDERR:", proc.stderr[:1000])
