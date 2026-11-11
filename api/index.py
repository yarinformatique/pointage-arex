import os
import sys
import json
import urllib.parse
import mimetypes
import datetime

# Add root folder to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database import init_db, get_connection
from logic import (
    get_settings, update_settings, process_scan,
    get_daily_dashboard, get_monthly_report
)
from export import export_daily_csv, export_monthly_csv

STATIC_DIR = os.path.join(ROOT_DIR, "static")

# Ensure DB initialized on cold start
try:
    init_db()
except Exception as e:
    print(f"Warning DB init: {e}")

def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()
    query_string = environ.get("QUERY_STRING", "")
    query = urllib.parse.parse_qs(query_string)

    def json_response(data, status="200 OK"):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        ]
        start_response(status, headers)
        return [body]

    def file_response(file_path, content_type, status="200 OK"):
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Fichier introuvable"]
        with open(file_path, "rb") as f:
            content = f.read()
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(content))),
            ("Cache-Control", "public, max-age=3600")
        ]
        start_response(status, headers)
        return [content]

    # CORS OPTIONS
    if method == "OPTIONS":
        headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        ]
        start_response("200 OK", headers)
        return [b""]

    # 1. Main View
    if path in ("/", "/index.html"):
        return file_response(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")

    # 2. Dedicated Mobile Scanner View
    if path in ("/scanner", "/scan", "/mobile", "/mobile.html"):
        return file_response(os.path.join(STATIC_DIR, "mobile.html"), "text/html; charset=utf-8")

    # 3. Static Files
    if path.startswith("/static/"):
        rel = path[len("/static/"):].replace("/", os.sep)
        full_p = os.path.join(STATIC_DIR, rel)
        mime, _ = mimetypes.guess_type(full_p)
        return file_response(full_p, mime or "application/octet-stream")

    # 4. API Endpoints
    if method == "GET":
        if path == "/api/dashboard":
            target_date = query.get("date", [None])[0]
            return json_response(get_daily_dashboard(target_date))

        if path == "/api/agents":
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM agents ORDER BY CAST(SUBSTR(matricule, 3) AS INTEGER), matricule")
            agents = [dict(a) for a in c.fetchall()]
            conn.close()
            return json_response(agents)

        if path == "/api/monthly":
            y = int(query.get("year", [datetime.datetime.now().year])[0])
            m = int(query.get("month", [datetime.datetime.now().month])[0])
            return json_response(get_monthly_report(y, m))

        if path == "/api/settings":
            return json_response(get_settings())

        if path == "/api/export/daily":
            d = query.get("date", [datetime.datetime.now().strftime("%Y-%m-%d")])[0]
            b = export_daily_csv(d)
            start_response("200 OK", [
                ("Content-Type", "text/csv; charset=utf-8-sig"),
                ("Content-Disposition", f'attachment; filename="Pointage_AREX_{d}.csv"'),
                ("Content-Length", str(len(b)))
            ])
            return [b]

        if path == "/api/export/monthly":
            now_dt = datetime.datetime.now()
            y = int(query.get("year", [now_dt.year])[0])
            m = int(query.get("month", [now_dt.month])[0])
            b = export_monthly_csv(y, m)
            start_response("200 OK", [
                ("Content-Type", "text/csv; charset=utf-8-sig"),
                ("Content-Disposition", f'attachment; filename="Pointage_AREX_Synthese_{y}_{m:02d}.csv"'),
                ("Content-Length", str(len(b)))
            ])
            return [b]

    elif method == "POST":
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
        except ValueError:
            content_length = 0
        raw_body = environ["wsgi.input"].read(content_length) if content_length > 0 else b"{}"
        try:
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception:
            body = {}

        if path == "/api/scan":
            res = process_scan(
                scan_input=body.get("scan_input", "").strip(),
                mode_scan=body.get("mode_scan", "MOBILE_CAMERA"),
                override_time=body.get("override_time"),
                override_date=body.get("override_date"),
                force_descente=bool(body.get("force_descente", False))
            )
            return json_response(res)

        if path == "/api/settings":
            update_settings(body)
            return json_response({"success": True, "settings": get_settings()})

        if path == "/api/override":
            code = str(body.get("code_superviseur", ""))
            settings = get_settings()
            if code != settings["code_superviseur"]:
                return json_response({"success": False, "message": "Code superviseur invalide"}, "403 Forbidden")
            
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
            return json_response({"success": True, "message": "Pointage régularisé avec succès."})

    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"Page non trouvee"]

# Alias for Vercel
application = app
