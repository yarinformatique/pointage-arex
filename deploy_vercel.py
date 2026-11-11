import subprocess
import os
import sys
import re
import webbrowser
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
NPX_CMD = r"C:\Program Files\nodejs\npx.cmd"

def banner():
    print("=" * 70)
    print("       POINTAGE AREX - DÉPLOIEMENT CLOUD VERCEL + SUPABASE")
    print("                Accessible 24h/24 dans le Monde Entier")
    print("=" * 70)
    print()

def is_vercel_logged_in():
    try:
        r = subprocess.run(
            [NPX_CMD, "--yes", "vercel", "whoami"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=15
        )
        out = (r.stdout + " " + r.stderr).strip()
        if r.returncode == 0 and "Logged out" not in out and len(out) > 0:
            return True, out.split("\n")[-1].strip()
        return False, None
    except Exception:
        return False, None

def update_desktop_files(prod_url):
    prod_url = prod_url.rstrip("/")
    if not prod_url.startswith("http"):
        prod_url = f"https://{prod_url}"

    scanner_url = f"{prod_url}/scanner"
    admin_url = f"{prod_url}/"

    content = f"""====================================================================
   POINTAGE AREX - LIENS OFFICIELS EN LIGNE (VERCEL + SUPABASE)
   Chantier & Direction - Bobo-Dioulasso, Burkina Faso
====================================================================

Accessible 24h/24 partout dans le monde en 4G/5G/Wi-Fi (Zéro interruption) :

📱 1. APPLICATION SMARTPHONE DU PROMOTEUR (SCANNER PUR) :
   👉 {scanner_url}

   (Interface ultra-rapide dédiée au promoteur sur le chantier.
    Ouvre directement la caméra plein écran pour scanner les badges.
    Bip sonore instantané et annonce vocale du statut : À l'heure / Retard).

--------------------------------------------------------------------

💻 2. TABLEAU DE BORD DIRECTION / RH / COMPTABILITÉ :
   👉 {admin_url}

   (Accès superviseur complet : arrivées, retards en minutes,
    absences, alertes sécurité, matrice mensuelle et exports Excel).

====================================================================
"""
    lien_file = os.path.join(DESKTOP_DIR, "LIEN_POINTAGE_AREX.txt")
    with open(lien_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("\n" + "=" * 70)
    print("          >>> DÉPLOIEMENT RÉUSSI SUR VERCEL ! <<<")
    print("=" * 70)
    print(f"\n[+] LIEN SMARTPHONE DU PROMOTEUR (SCANNER) :\n    {scanner_url}\n")
    print(f"[+] LIEN TABLEAU DE BORD DIRECTION (ADMIN)  :\n    {admin_url}\n")
    print(f"[OK] Fichier de liens enregistre sur le Bureau : LIEN_POINTAGE_AREX.txt")
    print("=" * 70)

    try:
        webbrowser.open(scanner_url)
    except Exception:
        pass

def main():
    banner()

    # Étape 1 : Vérification de la connexion Vercel
    logged_in, user = is_vercel_logged_in()
    if not logged_in:
        print("[ÉTAPE 1/2] Connexion à votre compte Vercel...")
        print("--------------------------------------------------------------------")
        print("👉 Une sélection va s'afficher ci-dessous.")
        print("👉 Appuyez sur ENTRÉE sur 'Continue with GitHub' (votre compte yarinformatique).")
        print("   Votre navigateur va s'ouvrir pour confirmer la connexion.")
        print("--------------------------------------------------------------------\n")
        try:
            subprocess.run([NPX_CMD, "--yes", "vercel", "login"], cwd=PROJECT_DIR)
        except Exception as e:
            print(f"[!] Erreur de commande vercel login : {e}")
    else:
        print(f"[OK] Déjà connecté à Vercel ({user}).\n")

    # Étape 2 : Déploiement en production
    print("\n[ÉTAPE 2/2] Déploiement de Pointage AREX en production sur Vercel...")
    print("--------------------------------------------------------------------")
    print("Configuration automatique : Python Serverless + Supabase PostgreSQL...")
    print("--------------------------------------------------------------------\n")

    try:
        # Run vercel deploy directly in console so user sees live build
        subprocess.run([NPX_CMD, "--yes", "vercel", "--prod", "--yes"], cwd=PROJECT_DIR)
    except Exception as e:
        print(f"[!] Erreur lors du déploiement : {e}")

    # Récupération automatique de l'URL déployée
    detected_url = None
    try:
        r = subprocess.run([NPX_CMD, "--yes", "vercel", "ls"], cwd=PROJECT_DIR, capture_output=True, text=True, timeout=15)
        matches = re.findall(r"https://[a-zA-Z0-9\.\-_]+\.vercel\.app", r.stdout + " " + r.stderr)
        if matches:
            detected_url = matches[0]
    except Exception:
        pass

    if not detected_url:
        detected_url = "https://pointage-arex.vercel.app"

    print("\n" + "-" * 70)
    print(f"URL détectée : {detected_url}")
    user_url = input(f"Confirmez l'URL Vercel affichée ci-dessus [Entrée pour '{detected_url}'] : ").strip()
    final_url = user_url if user_url else detected_url

    update_desktop_files(final_url)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[Erreur inattendue] : {e}")
    print()
    input("Appuyez sur ENTRÉE pour fermer cette fenêtre...")
