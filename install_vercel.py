import subprocess
import os

print("Starting npm install -g vercel...")
with open(r"C:\Users\USER\Desktop\pointage_arex\npm_install.log", "w", encoding="utf-8") as f:
    f.write("Installing vercel globally...\n")
    f.flush()
    try:
        p = subprocess.run(
            [r"C:\Program Files\nodejs\npm.CMD", "install", "-g", "vercel"],
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
        f.write(f"\nFinished with code {p.returncode}\n")
    except Exception as e:
        f.write(f"\nException: {e}\n")
print("Done installing vercel.")
