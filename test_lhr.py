import subprocess
import time
import re

cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:8080", "nokey@localhost.run"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

url = None
start = time.time()
while time.time() - start < 15:
    line = proc.stdout.readline()
    if not line:
        continue
    print("LINE:", line.strip())
    m = re.search(r"https://[a-zA-Z0-9\.\-]+\.lhr\.life", line)
    if m:
        url = m.group(0)
        print("FOUND_URL:", url)
        break

if not url:
    proc.terminate()
