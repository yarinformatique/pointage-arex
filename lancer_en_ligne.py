import subprocess
import sys
import os
import re
import time
import webbrowser
import socket
import threading

DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_EXE = os.path.join(PROJECT_DIR, "cloudflared.exe")
LOCAL_PORT = 8080

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_server_if_needed():
    if not is_port_open(LOCAL_PORT):
        print(f"[*] Démarrage du serveur Pointage Arex sur le port {LOCAL_PORT}...", flush=True)
        subprocess.Popen(
            [sys.executable, "app.py", str(LOCAL_PORT)],
            cwd=PROJECT_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        for _ in range(12):
            time.sleep(0.5)
            if is_port_open(LOCAL_PORT):
                break
        print(f"[OK] Serveur Pointage Arex prêt sur le port {LOCAL_PORT}.\n", flush=True)
    else:
        print(f"[OK] Serveur Pointage Arex déjà actif sur le port {LOCAL_PORT}.\n", flush=True)

def update_desktop_file(public_url):
    local_ip = get_local_ip()
    url_scanner = f"{public_url}/scanner"
    url_dashboard = f"{public_url}/"
    local_scanner = f"http://{local_ip}:{LOCAL_PORT}/scanner"

    content = f"""====================================================================
   POINTAGE AREX - LIENS OFFICIELS EN LIGNE (4G / WI-FI)
   Chantier & Direction - Bobo-Dioulasso, Burkina Faso
====================================================================

📱 1. LIEN DU PROMOTEUR SUR SMARTPHONE (APPLICATION SCANNER PURE) :
   👉 {url_scanner}

   (Sur smartphone, ce lien ouvre directement la caméra plein écran 
    avec bip sonore, validation vocale et grand badge du statut !)

--------------------------------------------------------------------

💻 2. LIEN DIRECTION / RH (TABLEAU DE BORD COMPLET & EXCEL) :
   👉 {url_dashboard}

   (Consultez les arrivées, retards, anomalies, et téléchargez Excel)

--------------------------------------------------------------------

📶 3. LIEN RÉSEAU LOCAL (Si connecté sur le même Wi-Fi au bureau) :
   👉 {local_scanner}
   👉 http://localhost:{LOCAL_PORT}

====================================================================
⚠️ NOTE IMPORTANTE :
Laissez la fenêtre noire du lanceur ouverte pendant que la plateforme
est utilisée par vos équipes sur le terrain.
====================================================================
"""
    file_path = os.path.join(DESKTOP_DIR, "LIEN_POINTAGE_AREX.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Fichier 'LIEN_POINTAGE_AREX.txt' actualisé sur votre Bureau !\n", flush=True)
    except Exception as e:
        print(f"[!] Erreur écriture fichier: {e}")

def start_tunnel():
    if not os.path.exists(CLOUDFLARED_EXE):
        print(f"[!] cloudflared.exe introuvable dans {PROJECT_DIR}.")
        print("[!] Lancement en local uniquement.")
        webbrowser.open(f"http://localhost:{LOCAL_PORT}/scanner")
        return

    print("====================================================================")
    print("      LANCEMENT DU TUNNEL SÉCURISÉ INTERNET CLOUDFLARE...")
    print("====================================================================")
    print("[*] Négociation du lien sécurisé mondial en cours...", flush=True)

    cmd = [CLOUDFLARED_EXE, "tunnel", "--url", f"http://127.0.0.1:{LOCAL_PORT}"]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    url_found = False
    public_url = None

    def read_stream(stream):
        nonlocal url_found, public_url
        for line in iter(stream.readline, ""):
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match and not url_found:
                url_found = True
                public_url = match.group(0)
                url_scanner = f"{public_url}/scanner"
                
                print("\n====================================================================")
                print("   🌟 PLATEFORME POINTAGE AREX EN LIGNE AVEC SUCCÈS ! 🌟")
                print("====================================================================")
                print(f"📱 LIEN SCANNER SMARTPHONE  : {url_scanner}")
                print(f"📊 LIEN TABLEAU DE BORD      : {public_url}")
                print("====================================================================")
                print("[*] Gardez cette fenêtre ouverte tant que les pointages ont lieu.")
                print("====================================================================\n")
                
                update_desktop_file(public_url)
                try:
                    webbrowser.open(url_scanner)
                except Exception:
                    pass

    t_err = threading.Thread(target=read_stream, args=(process.stderr,), daemon=True)
    t_out = threading.Thread(target=read_stream, args=(process.stdout,), daemon=True)
    t_err.start()
    t_out.start()

    # Progress feedback while connecting
    for i in range(25):
        if url_found:
            break
        time.sleep(1)
        print(".", end="", flush=True)
    print()

    if not url_found:
        print("[!] La connexion Cloudflare a pris plus de temps que prévu.")
        print(f"[!] Ouverture en local : http://localhost:{LOCAL_PORT}/scanner")
        webbrowser.open(f"http://localhost:{LOCAL_PORT}/scanner")

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nArrêt du tunnel et du serveur...")
        process.terminate()

def main():
    start_server_if_needed()
    start_tunnel()

if __name__ == "__main__":
    main()
