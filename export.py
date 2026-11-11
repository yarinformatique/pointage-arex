import io
import csv
import zipfile
import xml.etree.ElementTree as ET
from logic import get_daily_dashboard, get_monthly_report

def export_daily_csv(target_date):
    data = get_daily_dashboard(target_date)
    output = io.StringIO()
    # Write UTF-8 BOM for Excel compatibility
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')

    # Header title
    writer.writerow(["POINTAGE AREX - FEUILLE DU JOUR", target_date])
    writer.writerow([])
    writer.writerow([
        "Matricule", "Nom", "Prénom", "Identité", "Fonction", 
        "Heure Arrivée", "Statut Arrivée", "Retard (min)", 
        "Heure Descente", "Statut Descente", "Temps Travail", "État du Jour", "Note"
    ])

    for item in data["agents_table"]:
        a = item["agent"]
        pt = item["pointage"] or {}
        etat = item["etat"]
        
        arr = pt.get("heure_arrivee") or ""
        statut_arr = pt.get("statut_arrivee") or ""
        retard = pt.get("minutes_retard") or 0
        des = pt.get("heure_descente") or ""
        statut_des = pt.get("statut_descente") or ""
        temps = f"{pt.get('temps_travail_minutes', 0) // 60}h {pt.get('temps_travail_minutes', 0) % 60:02d}m" if pt.get("temps_travail_minutes") else ""
        note = pt.get("note") or ""

        # Friendly labels
        statut_arr_label = {
            "A_L_HEURE": "À l'heure",
            "RETARD": "En retard",
            "HORS_DELAI": "Hors délai",
            "NON_POINTE": "Non pointé"
        }.get(statut_arr, statut_arr)

        statut_des_label = {
            "VALIDE": "Validée",
            "ANTICIPE_AUTORISE": "Sortie anticipée",
            "SANS_ARRIVEE": "Descente sans arrivée (Anomalie)"
        }.get(statut_des, statut_des)

        etat_label = {
            "PRESENT": "Présent (Arrivée faite)",
            "DESCENTE": "Journée clôturée (Descente faite)",
            "ABSENT": "Absent",
            "ANOMALIE": "Anomalie sécurité"
        }.get(etat, etat)

        writer.writerow([
            a["matricule"], a["nom"], a["prenom"], a["identite"], a["fonction"],
            arr, statut_arr_label, retard if retard > 0 else 0,
            des, statut_des_label, temps, etat_label, note
        ])

    return output.getvalue().encode('utf-8-sig')

def export_monthly_csv(year, month):
    data = get_monthly_report(year, month)
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')

    writer.writerow(["POINTAGE AREX - SYNTHÈSE MENSUELLE", f"{year}-{int(month):02d}"])
    writer.writerow([f"Jours ouvrés observés : {data['nb_jours_ouvres']}"])
    writer.writerow([])
    writer.writerow([
        "Matricule", "Identité", "Fonction", 
        "À l'heure", "En retard", "Hors délai", 
        "Descentes", "Total Présences", "Absences", 
        "Total Heures", "Taux Assiduité (%)"
    ])

    for row in data["summary"]:
        a = row["agent"]
        writer.writerow([
            a["matricule"], a["identite"], a["fonction"],
            row["a_l_heure"], row["retard"], row["hors_delai"],
            row["descentes"], row["total_presents"], row["absences"],
            str(row["total_heures"]).replace('.', ','),
            f"{row['taux_assiduite']}%"
        ])

    return output.getvalue().encode('utf-8-sig')
