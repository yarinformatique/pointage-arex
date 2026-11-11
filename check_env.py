import os
import sys
import shutil
import subprocess

with open(r"C:\Users\USER\Desktop\pointage_arex\env_results.txt", "w", encoding="utf-8") as f:
    f.write("=== ENVIRONMENT CHECK ===\n")
    for cmd in ["node", "npm", "npx", "git", "python", "vercel", "gh"]:
        p = shutil.which(cmd)
        f.write(f"{cmd}: {p}\n")
    f.flush()

    try:
        r = subprocess.run("git status", shell=True, capture_output=True, text=True, cwd=r"C:\Users\USER\Desktop\pointage_arex")
        f.write("\n=== GIT STATUS ===\n" + r.stdout + "\n" + r.stderr + "\n")
    except Exception as e:
        f.write(f"\nGit error: {e}\n")
    f.flush()

    try:
        r = subprocess.run("node -v", shell=True, capture_output=True, text=True)
        f.write(f"\nNode version: {r.stdout.strip()} (err: {r.stderr.strip()})\n")
    except Exception as e:
        f.write(f"\nNode error: {e}\n")
    f.flush()

    try:
        r = subprocess.run("npx --version", shell=True, capture_output=True, text=True)
        f.write(f"\nNPX version: {r.stdout.strip()} (err: {r.stderr.strip()})\n")
    except Exception as e:
        f.write(f"\nNPX error: {e}\n")
    f.flush()

    try:
        r = subprocess.run("vercel --version", shell=True, capture_output=True, text=True)
        f.write(f"\nVercel CLI direct: {r.stdout.strip()} (err: {r.stderr.strip()})\n")
    except Exception as e:
        f.write(f"\nVercel direct error: {e}\n")
    f.flush()

    f.write("\nDONE!\n")
