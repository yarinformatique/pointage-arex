import subprocess
import os

repo_dir = r"C:\Users\USER\Desktop\pointage_arex"

def run_git(args):
    r = subprocess.run(["git"] + args, cwd=repo_dir, capture_output=True, text=True)
    print(f"git {' '.join(args)} -> {r.returncode}")
    if r.stdout: print(r.stdout.strip())
    if r.stderr: print(r.stderr.strip())
    return r.returncode

if not os.path.exists(os.path.join(repo_dir, ".git")):
    run_git(["init"])
    run_git(["config", "user.name", "YAGO Abdoul Rachide"])
    run_git(["config", "user.email", "yarinformatique@gmail.com"])
    run_git(["add", "."])
    run_git(["commit", "-m", "Initial commit Pointage AREX BTP"])
    run_git(["branch", "-M", "main"])
else:
    run_git(["status"])
