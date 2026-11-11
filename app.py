import http.server
import socketserver
import json
import urllib.parse
import os
import mimetypes
import sys
import datetime

from database import init_db, get_connection
from logic import (
    get_settings, update_settings, process_scan, 
    get_daily_dashboard, get_monthly_report
)
from export import export_daily_csv, export_monthly_csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

class PointageRequestHandler(http.server.BaseHTTPRequestHandler):
    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Main index.html
        if path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
            self.serve_file(file_path, "text/html; charset=utf-8")
            return

        # 1-bis. Dedicated Mobile Scanner view (/scanner, /mobile, /scan)
        if path in ("/scanner", "/mobile", "/scan", "/mobile.html"):
            file_path = os.path.join(STATIC_DIR, "mobile.html")
            self.serve_file(file_path, "text/html; charset=utf-8")
            return

        # 2. Static files
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):].replace("/", os.sep)
            file_path = os.path.join(STATIC_DIR, rel_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            self.serve_file(file_path, mime_type or "application/octet-stream")
            return

        # 3. API Dashboard
        if path == "/api/dashboard":
            target_date = query.get("date", [None])[0]
            data = get_daily_dashboard(target_date)
            self.send_json(data)
            return

        # 4. API Agents
        if path == "/api/agents":
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM agents ORDER BY CAST(SUBSTR(matricule, 3) AS INTEGER), matricule")
            agents = [dict(a) for a in c.fetchall()]
            conn.close()
            self.send_json(agents)
            return

        # 5. API Monthly
        if path == "/api/monthly":
            year = int(query.get("year", [datetime.datetime.now().year])[0])
            month = int(query.get("month", [datetime.datetime.now().month])[0])
            data = get_monthly_report(year, month)
            self.send_json(data)
            return

        # 6. API Settings
        if path == "/api/settings":
            self.send_json(get_settings())
            return

        # 7. Exports
        if path == "/api/export/daily":
            target_date = query.get("date", [datetime.datetime.now().strftime("%Y-%m-%d")])[0]
            csv_bytes = export_daily_csv(target_date)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8-sig")
            self.send_header("Content-Disposition", f'attachment; filename="Pointage_AREX_{target_date}.csv"')
            self.send_header("Content-Length", str(len(csv_bytes)))
            self.end_headers()
            self.wfile.write(csv_bytes)
            return

        if path == "/api/export/monthly":
            now_dt = datetime.datetime.now()
            year = int(query.get("year", [now_dt.year])[0])
            month = int(query.get("month", [now_dt.month])[0])
            csv_bytes = export_monthly_csv(year, month)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8-sig")
            self.send_header("Content-Disposition", f'attachment; filename="Pointage_AREX_Synthese_{year}_{month:02d}.csv"')
            self.send_header("Content-Length", str(len(csv_bytes)))
            self.end_headers()
            self.wfile.write(csv_bytes)
            return

        self.send_error(404, "Page non trouvée")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        # 1. API Scan
        if path == "/api/scan":
            scan_input = body.get("scan_input", "").strip()
            mode_scan = body.get("mode_scan", "QR_CAMERA")
            override_time = body.get("override_time")
            override_date = body.get("override_date")
            force_descente = bool(body.get("force_descente", False))
            
            res = process_scan(
                scan_input=scan_input,
                mode_scan=mode_scan,
                override_time=override_time,
                override_date=override_date,
                force_descente=force_descente
            )
            self.send_json(res)
            return

        # 2. API Settings Update
        if path == "/api/settings":
            update_settings(body)
            self.send_json({"success": True, "settings": get_settings()})
            return

        # 3. Add Agent
        if path == "/api/agents":
            matricule = body.get("matricule", "").strip()
            nom = body.get("nom", "").strip().upper()
            prenom = body.get("prenom", "").strip()
            fonction = body.get("fonction", "Ouvrier").strip()
            telephone = body.get("telephone", "").strip()
            identite = f"{matricule} {nom} {prenom}".strip()
            gurl = f"https://docs.google.com/forms/d/e/1FAIpQLSdoQrCfoN8x5TxD2rgJJwzlw_oWUJmKuaCHDm00tYADJH-98w/formResponse?entry.1849590193={identite.replace(' ', '+')}"

            conn = get_connection()
            c = conn.cursor()
            try:
                c.execute("""
                    INSERT INTO agents (matricule, nom, prenom, identite, fonction, telephone, google_form_url, actif, date_creation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (matricule, nom, prenom, identite, fonction, telephone, gurl, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                new_id = c.lastrowid
                conn.close()
                self.send_json({"success": True, "id": new_id, "matricule": matricule})
            except Exception as e:
                conn.close()
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        # 4. Superviseur Override / Regularisation
        if path == "/api/override":
            code = str(body.get("code_superviseur", ""))
            settings = get_settings()
            if code != settings["code_superviseur"]:
                self.send_json({"success": False, "message": "Code superviseur invalide"}, 403)
                return

            agent_id = body.get("agent_id")
            target_date = body.get("date")
            heure_arr = body.get("heure_arrivee")
            statut_arr = body.get("statut_arrivee")
            heure_des = body.get("heure_descente")
            statut_des = body.get("statut_descente")
            note = body.get("note", "Régularisation superviseur")

            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT id FROM pointages WHERE agent_id = ? AND date = ?", (agent_id, target_date))
            existing = c.fetchone()
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if existing:
                c.execute("""
                    UPDATE pointages
                    SET heure_arrivee = ?, statut_arrivee = ?, heure_descente = ?, statut_descente = ?, note = ?, updated_at = ?
                    WHERE id = ?
                """, (heure_arr, statut_arr, heure_des, statut_des, note, now_str, existing["id"]))
            else:
                c.execute("""
                    INSERT INTO pointages (agent_id, date, heure_arrivee, statut_arrivee, heure_descente, statut_descente, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (agent_id, target_date, heure_arr, statut_arr, heure_des, statut_des, note, now_str, now_str))
            
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Pointage régularisé avec succès."})
            return

        self.send_error(404, "Endpoint non trouvé")

    def serve_file(self, file_path, content_type):
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_error(404, "Fichier non trouvé")
            return
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Erreur serveur : {e}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run_server(port=8080):
    init_db()
    server_address = ("0.0.0.0", port)
    httpd = ThreadedHTTPServer(server_address, PointageRequestHandler)
    print(f"================================================================")
    print(f"   PLATEFORME DE POINTAGE AREX - GÉNIE CIVIL (BOBO-DIOULASSO)")
    print(f"================================================================")
    print(f"[*] Serveur actif en local sur : http://localhost:{port}")
    print(f"[*] Accès réseau local Wi-Fi  : http://[VOTRE_IP_LOCALE]:{port}")
    print(f"================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        httpd.server_close()

if __name__ == "__main__":
    p = 8080
    if len(sys.argv) > 1:
        try:
            p = int(sys.argv[1])
        except ValueError:
            pass
    run_server(p)
