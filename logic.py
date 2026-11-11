import re
import datetime
import urllib.parse
from database import get_connection

def get_settings():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT cle, valeur FROM parametres")
    rows = c.fetchall()
    conn.close()
    params = {r["cle"]: r["valeur"] for r in rows}
    return {
        "nom_entreprise": params.get("nom_entreprise", "POINTAGE AREX"),
        "sous_titre": params.get("sous_titre", "Génie Civil & BTP - Bobo-Dioulasso, Burkina Faso"),
        "heure_arrivee_debut": params.get("heure_arrivee_debut", "06:00"),
        "heure_arrivee_limite": params.get("heure_arrivee_limite", "07:30"),
        "heure_retard_limite": params.get("heure_retard_limite", "09:00"),
        "heure_descente_debut": params.get("heure_descente_debut", "16:00"),
        "antirebond_secondes": int(params.get("antirebond_secondes", "60")),
        "code_superviseur": params.get("code_superviseur", "1234"),
        "auto_absent_apres_9h": params.get("auto_absent_apres_9h", "1")
    }

def update_settings(new_params):
    conn = get_connection()
    c = conn.cursor()
    for k, v in new_params.items():
        c.execute("INSERT OR REPLACE INTO parametres (cle, valeur) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()

def parse_time_str(t_str):
    if not t_str:
        return None
    parts = [int(p) for p in t_str.split(":")]
    if len(parts) == 2:
        return datetime.time(parts[0], parts[1], 0)
    elif len(parts) == 3:
        return datetime.time(parts[0], parts[1], parts[2])
    return None

def time_to_seconds(t):
    return t.hour * 3600 + t.minute * 60 + t.second

def diff_in_minutes(t_early, t_late):
    sec = time_to_seconds(t_late) - time_to_seconds(t_early)
    return max(0, sec // 60)

def resolve_agent(scan_string):
    if not scan_string:
        return None
    raw = scan_string.strip()
    conn = get_connection()
    c = conn.cursor()

    # 1. Check if raw matches Google Form response URL
    # e.g.: https://docs.google.com/forms/d/e/.../formResponse?entry.1849590193=Ag1+BAZIE+LAURENT
    if "entry." in raw:
        match = re.search(r"entry\.\d+=([^&]+)", raw)
        if match:
            extracted = urllib.parse.unquote_plus(match.group(1)).strip()
            # Try to match matricule from extracted e.g. "Ag1 BAZIE LAURENT" -> "Ag1"
            m_match = re.match(r"^(Ag\d+)", extracted, re.IGNORECASE)
            if m_match:
                mlle = m_match.group(1).capitalize()
                c.execute("SELECT * FROM agents WHERE UPPER(matricule) = UPPER(?) AND actif = 1", (mlle,))
                res = c.fetchone()
                if res:
                    conn.close()
                    return dict(res)
            # Or match full identity
            c.execute("SELECT * FROM agents WHERE UPPER(identite) = UPPER(?) AND actif = 1", (extracted,))
            res = c.fetchone()
            if res:
                conn.close()
                return dict(res)

    # 2. Check if raw matches matricule directly (Ag1, ag12, etc.)
    m_match = re.match(r"^(Ag\d+)$", raw, re.IGNORECASE)
    if m_match:
        mlle = m_match.group(1)
        c.execute("SELECT * FROM agents WHERE UPPER(matricule) = UPPER(?) AND actif = 1", (mlle,))
        res = c.fetchone()
        if res:
            conn.close()
            return dict(res)

    # 3. Check if raw begins with Ag1, Ag2, etc. (e.g. "Ag1 BAZIE LAURENT")
    m_start = re.match(r"^(Ag\d+)\b", raw, re.IGNORECASE)
    if m_start:
        mlle = m_start.group(1)
        c.execute("SELECT * FROM agents WHERE UPPER(matricule) = UPPER(?) AND actif = 1", (mlle,))
        res = c.fetchone()
        if res:
            conn.close()
            return dict(res)

    # 4. Search by exact identite or nom + prenom
    c.execute("SELECT * FROM agents WHERE UPPER(identite) = UPPER(?) AND actif = 1", (raw,))
    res = c.fetchone()
    if res:
        conn.close()
        return dict(res)

    # 5. Fuzzy match by NOM or PRENOM
    clean_search = raw.replace("%", "").strip()
    if len(clean_search) >= 3:
        c.execute("""
            SELECT * FROM agents 
            WHERE (UPPER(nom) = UPPER(?) OR UPPER(identite) LIKE UPPER(?) OR UPPER(matricule) = UPPER(?))
              AND actif = 1
        """, (clean_search, f"%{clean_search}%", clean_search))
        res = c.fetchone()
        if res:
            conn.close()
            return dict(res)

    conn.close()
    return None

def process_scan(scan_input, mode_scan="QR_CAMERA", override_time=None, override_date=None, force_descente=False):
    settings = get_settings()
    now_dt = datetime.datetime.now()
    
    current_date = override_date or now_dt.strftime("%Y-%m-%d")
    current_time_str = override_time or now_dt.strftime("%H:%M:%S")
    current_time = parse_time_str(current_time_str)

    t_arr_start = parse_time_str(settings["heure_arrivee_debut"])
    t_arr_limit = parse_time_str(settings["heure_arrivee_limite"])
    t_ret_limit = parse_time_str(settings["heure_retard_limite"])
    t_des_start = parse_time_str(settings["heure_descente_debut"])

    agent = resolve_agent(scan_input)
    conn = get_connection()
    c = conn.cursor()

    if not agent:
        # Record anomaly: Agent Inconnu
        c.execute("""
            INSERT INTO anomalies (agent_id, date, heure, type, details, created_at)
            VALUES (NULL, ?, ?, 'AGENT_INCONNU', ?, ?)
        """, (current_date, current_time_str, f"Scan non reconnu: {scan_input[:100]}", now_dt.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return {
            "success": False,
            "status": "AGENT_INCONNU",
            "message": f"Badge non reconnu : '{scan_input}'",
            "audio": "alarm",
            "date": current_date,
            "time": current_time_str
        }

    agent_id = agent["id"]

    # Check existing pointage for today
    c.execute("SELECT * FROM pointages WHERE agent_id = ? AND date = ?", (agent_id, current_date))
    pointage = c.fetchone()

    # =========================================================================
    # CASE 1: AUCUN POINTAGE POUR AUJOURD'HUI
    # =========================================================================
    if not pointage:
        # A) Scan à partir de l'heure de descente (>= 16h00) SANS ARRIVÉE
        if current_time >= t_des_start and not force_descente:
            # Sécurité stricte : Tentative de descente sans arrivée
            c.execute("""
                INSERT INTO pointages (
                    agent_id, date, heure_arrivee, statut_arrivee, minutes_retard,
                    heure_descente, statut_descente, temps_travail_minutes, note,
                    mode_scan_arrivee, mode_scan_descente, created_at, updated_at
                ) VALUES (?, ?, NULL, 'NON_POINTE', 0, ?, 'SANS_ARRIVEE', 0, ?, NULL, ?, ?, ?)
            """, (
                agent_id, current_date, current_time_str,
                "Anomalie de sécurité : Scan de départ à 16h+ sans arrivée pointée le matin",
                mode_scan, now_dt.strftime("%Y-%m-%d %H:%M:%S"), now_dt.strftime("%Y-%m-%d %H:%M:%S")
            ))
            pointage_id = c.lastrowid

            # Enregistrement dans la table des anomalies
            c.execute("""
                INSERT INTO anomalies (agent_id, date, heure, type, details, created_at)
                VALUES (?, ?, ?, 'DESCENTE_SANS_ARRIVEE', ?, ?)
            """, (
                agent_id, current_date, current_time_str,
                f"L'agent {agent['identite']} a scanné à {current_time_str} sans pointage d'arrivée le matin.",
                now_dt.strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            conn.close()

            return {
                "success": True,
                "security_alert": True,
                "status": "ANOMALIE_SECURITE",
                "sub_status": "DESCENTE_SANS_ARRIVEE",
                "message": f"⚠️ ALERTE SÉCURITÉ : Descente scannée à {current_time_str[:5]}, mais ARRIVÉE NON POINTÉE ce matin ! Pointage signalé aux RH.",
                "audio": "alarm",
                "agent": dict(agent),
                "pointage": {
                    "id": pointage_id,
                    "date": current_date,
                    "heure_arrivee": None,
                    "statut_arrivee": "NON_POINTE",
                    "heure_descente": current_time_str,
                    "statut_descente": "SANS_ARRIVEE"
                }
            }

        # B) Scan normal d'arrivée (< 16h00 ou forcé)
        if current_time <= t_arr_limit:
            statut = "A_L_HEURE"
            retard = 0
            msg = f"ARRIVÉE À L'HEURE à {current_time_str[:5]}"
            sub_msg = "Ponctualité parfaite. Bonne journée !"
            audio = "success"
        elif current_time <= t_ret_limit:
            statut = "RETARD"
            retard = diff_in_minutes(t_arr_limit, current_time)
            msg = f"ARRIVÉE EN RETARD à {current_time_str[:5]}"
            sub_msg = f"+{retard} min de retard (tolérance 07h30 dépassée)."
            audio = "warning"
        else:
            statut = "HORS_DELAI"
            retard = diff_in_minutes(t_arr_limit, current_time)
            msg = f"ARRIVÉE HORS DÉLAI à {current_time_str[:5]}"
            sub_msg = f"+{retard} min de retard (après 09h00)."
            audio = "danger"

        c.execute("""
            INSERT INTO pointages (
                agent_id, date, heure_arrivee, statut_arrivee, minutes_retard,
                heure_descente, statut_descente, temps_travail_minutes, note,
                mode_scan_arrivee, mode_scan_descente, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, NULL, NULL, 0, '', ?, NULL, ?, ?)
        """, (
            agent_id, current_date, current_time_str, statut, retard,
            mode_scan, now_dt.strftime("%Y-%m-%d %H:%M:%S"), now_dt.strftime("%Y-%m-%d %H:%M:%S")
        ))
        pointage_id = c.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "security_alert": False,
            "status": "SUCCESS_ARRIVEE",
            "statut_arrivee": statut,
            "minutes_retard": retard,
            "message": msg,
            "sub_message": sub_msg,
            "audio": audio,
            "agent": dict(agent),
            "pointage": {
                "id": pointage_id,
                "date": current_date,
                "heure_arrivee": current_time_str,
                "statut_arrivee": statut,
                "minutes_retard": retard,
                "heure_descente": None,
                "statut_descente": None
            }
        }

    # =========================================================================
    # CASE 2: UN POINTAGE EXISTE DÉJÀ AUJOURD'HUI
    # =========================================================================
    pt = dict(pointage)

    # 1. Si la descente est déjà validée
    if pt["heure_descente"]:
        conn.close()
        return {
            "success": False,
            "status": "DEJA_COMPLET",
            "message": f"Pointage déjà COMPLET pour aujourd'hui : Arrivée {pt['heure_arrivee'][:5] if pt['heure_arrivee'] else 'N/A'}, Descente {pt['heure_descente'][:5]}.",
            "sub_message": "Les deux pointages ont déjà été validés.",
            "audio": "info",
            "agent": dict(agent),
            "pointage": pt
        }

    # 2. Protection Anti-Rebond (Scan trop rapproché)
    if pt["heure_arrivee"]:
        t_arr = parse_time_str(pt["heure_arrivee"])
        diff_sec = time_to_seconds(current_time) - time_to_seconds(t_arr)
        if 0 <= diff_sec < settings["antirebond_secondes"]:
            conn.close()
            return {
                "success": False,
                "status": "ANTI_REBOND",
                "message": f"Badge déjà scanné à l'instant ({pt['heure_arrivee'][:5]}).",
                "sub_message": f"Veuillez patienter ({settings['antirebond_secondes'] - diff_sec}s restantes).",
                "audio": "info",
                "agent": dict(agent),
                "pointage": pt
            }

    # 3. Scan pour la DESCENTE (Heure >= 16h00 ou forcé par superviseur)
    if current_time >= t_des_start or force_descente:
        # Calcul du temps de présence
        temps_minutes = 0
        temps_str = ""
        if pt["heure_arrivee"]:
            t_arr = parse_time_str(pt["heure_arrivee"])
            temps_minutes = max(0, (time_to_seconds(current_time) - time_to_seconds(t_arr)) // 60)
            h = temps_minutes // 60
            m = temps_minutes % 60
            temps_str = f"{h}h {m:02d}min"
        else:
            temps_str = "Durée inconnue (arrivée non pointée)"

        statut_des = "VALIDE" if current_time >= t_des_start else "ANTICIPE_AUTORISE"

        c.execute("""
            UPDATE pointages
            SET heure_descente = ?, statut_descente = ?, temps_travail_minutes = ?,
                mode_scan_descente = ?, updated_at = ?
            WHERE id = ?
        """, (current_time_str, statut_des, temps_minutes, mode_scan, now_dt.strftime("%Y-%m-%d %H:%M:%S"), pt["id"]))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "security_alert": False,
            "status": "SUCCESS_DESCENTE",
            "statut_descente": statut_des,
            "message": f"DESCENTE VALIDÉE à {current_time_str[:5]}",
            "sub_message": f"Temps de travail : {temps_str}. Bonne fin de journée !",
            "audio": "departure",
            "agent": dict(agent),
            "pointage": {
                **pt,
                "heure_descente": current_time_str,
                "statut_descente": statut_des,
                "temps_travail_minutes": temps_minutes
            }
        }

    # 4. Scan avant 16h00 alors que l'arrivée est déjà faite
    conn.close()
    return {
        "success": False,
        "status": "DEPART_ANTICIPE_BLOQUE",
        "message": f"Arrivée déjà validée à {pt['heure_arrivee'][:5]} ({pt['statut_arrivee']}).",
        "sub_message": f"Descente autorisée seulement à partir de {settings['heure_descente_debut']}.",
        "can_override": True,
        "audio": "warning",
        "agent": dict(agent),
        "pointage": pt
    }

def get_daily_dashboard(target_date=None):
    now_dt = datetime.datetime.now()
    date_str = target_date or now_dt.strftime("%Y-%m-%d")
    settings = get_settings()

    conn = get_connection()
    c = conn.cursor()

    # Total agents
    c.execute("SELECT * FROM agents WHERE actif = 1 ORDER BY CAST(SUBSTR(matricule, 3) AS INTEGER), matricule")
    all_agents = [dict(a) for a in c.fetchall()]
    total_effectif = len(all_agents)

    # All pointages of the day
    c.execute("""
        SELECT p.*, a.matricule, a.nom, a.prenom, a.identite, a.fonction
        FROM pointages p
        JOIN agents a ON p.agent_id = a.id
        WHERE p.date = ?
        ORDER BY p.updated_at DESC
    """, (date_str,))
    pointages = [dict(p) for p in c.fetchall()]
    pointages_by_agent_id = {p["agent_id"]: p for p in pointages}

    # All anomalies of the day
    c.execute("""
        SELECT an.*, a.matricule, a.nom, a.prenom, a.identite, a.fonction
        FROM anomalies an
        LEFT JOIN agents a ON an.agent_id = a.id
        WHERE an.date = ?
        ORDER BY an.id DESC
    """, (date_str,))
    anomalies = [dict(an) for an in c.fetchall()]

    conn.close()

    nb_a_l_heure = sum(1 for p in pointages if p["statut_arrivee"] == "A_L_HEURE")
    nb_retard = sum(1 for p in pointages if p["statut_arrivee"] == "RETARD")
    nb_hors_delai = sum(1 for p in pointages if p["statut_arrivee"] == "HORS_DELAI")
    nb_descentes = sum(1 for p in pointages if p["heure_descente"] is not None)
    nb_sans_arrivee = sum(1 for p in pointages if p["statut_descente"] == "SANS_ARRIVEE")
    nb_presents = sum(1 for p in pointages if p["statut_arrivee"] in ("A_L_HEURE", "RETARD", "HORS_DELAI"))
    nb_absents = total_effectif - nb_presents

    taux_presence = round((nb_presents / total_effectif * 100), 1) if total_effectif > 0 else 0
    taux_ponctualite = round((nb_a_l_heure / nb_presents * 100), 1) if nb_presents > 0 else 0

    # Build agent status list for table
    agents_table = []
    for a in all_agents:
        aid = a["id"]
        pt = pointages_by_agent_id.get(aid)
        if pt:
            etat = "PRESENT"
            if pt["heure_descente"]:
                etat = "DESCENTE"
            if pt["statut_descente"] == "SANS_ARRIVEE":
                etat = "ANOMALIE"
            agents_table.append({
                "agent": a,
                "pointage": pt,
                "etat": etat
            })
        else:
            agents_table.append({
                "agent": a,
                "pointage": None,
                "etat": "ABSENT"
            })

    return {
        "date": date_str,
        "settings": settings,
        "kpis": {
            "total_effectif": total_effectif,
            "nb_presents": nb_presents,
            "nb_a_l_heure": nb_a_l_heure,
            "nb_retard": nb_retard,
            "nb_hors_delai": nb_hors_delai,
            "nb_descentes": nb_descentes,
            "nb_sans_arrivee": nb_sans_arrivee,
            "nb_absents": nb_absents,
            "taux_presence": taux_presence,
            "taux_ponctualite": taux_ponctualite
        },
        "agents_table": agents_table,
        "recent_pointages": pointages[:20],
        "anomalies": anomalies
    }

def get_monthly_report(year, month):
    conn = get_connection()
    c = conn.cursor()

    # Get all active agents
    c.execute("SELECT * FROM agents WHERE actif = 1 ORDER BY CAST(SUBSTR(matricule, 3) AS INTEGER), matricule")
    agents = [dict(a) for a in c.fetchall()]

    prefix = f"{year}-{int(month):02d}-%"
    c.execute("""
        SELECT * FROM pointages
        WHERE date LIKE ?
    """, (prefix,))
    all_month_pointages = [dict(p) for p in c.fetchall()]

    # Group by agent_id
    by_agent = {}
    for pt in all_month_pointages:
        aid = pt["agent_id"]
        if aid not in by_agent:
            by_agent[aid] = []
        by_agent[aid].append(pt)

    # Distinct dates in month with at least one pointage
    distinct_dates = set(p["date"] for p in all_month_pointages)
    nb_jours_ouvres = len(distinct_dates) if distinct_dates else 1

    summary = []
    for a in agents:
        pts = by_agent.get(a["id"], [])
        a_l_heure = sum(1 for p in pts if p["statut_arrivee"] == "A_L_HEURE")
        retard = sum(1 for p in pts if p["statut_arrivee"] == "RETARD")
        hors_delai = sum(1 for p in pts if p["statut_arrivee"] == "HORS_DELAI")
        descentes = sum(1 for p in pts if p["heure_descente"] is not None)
        total_presents = a_l_heure + retard + hors_delai
        total_absences = max(0, nb_jours_ouvres - total_presents)
        total_minutes = sum(p["temps_travail_minutes"] or 0 for p in pts)
        
        summary.append({
            "agent": a,
            "a_l_heure": a_l_heure,
            "retard": retard,
            "hors_delai": hors_delai,
            "descentes": descentes,
            "total_presents": total_presents,
            "absences": total_absences,
            "total_heures": round(total_minutes / 60, 1),
            "taux_assiduite": round((total_presents / nb_jours_ouvres * 100), 1) if nb_jours_ouvres > 0 else 0
        })

    conn.close()
    return {
        "year": year,
        "month": month,
        "nb_jours_ouvres": nb_jours_ouvres,
        "summary": summary
    }
