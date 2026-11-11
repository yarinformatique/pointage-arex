import sys
from logic import process_scan, resolve_agent, get_daily_dashboard
from database import get_connection

# Clear test date
conn = get_connection()
conn.execute("DELETE FROM pointages WHERE date = '2026-11-09'")
conn.execute("DELETE FROM anomalies WHERE date = '2026-11-09'")
conn.commit()
conn.close()

print("--- Test 1: Resolve Google Form URL ---")
url = "https://docs.google.com/forms/d/e/1FAIpQLSdoQrCfoN8x5TxD2rgJJwzlw_oWUJmKuaCHDm00tYADJH-98w/formResponse?entry.1849590193=Ag1+BAZIE+LAURENT"
ag = resolve_agent(url)
print("Resolved:", ag["matricule"])
assert ag["matricule"] == "Ag1"

print("\n--- Test 2: Scan Arrivée à l'heure (07:15) ---")
res2 = process_scan("Ag1", override_date="2026-11-09", override_time="07:15:00")
print("Status:", res2["status"])
assert res2["statut_arrivee"] == "A_L_HEURE"

print("\n--- Test 3: Anti-rebond (07:15:20) ---")
res3 = process_scan("Ag1", override_date="2026-11-09", override_time="07:15:20")
print("Status:", res3["status"])
assert res3["status"] == "ANTI_REBOND"

print("\n--- Test 4: Depart bloque avant 16h (12:00) ---")
res4 = process_scan("Ag1", override_date="2026-11-09", override_time="12:00:00")
print("Status:", res4["status"])
assert res4["status"] == "DEPART_ANTICIPE_BLOQUE"

print("\n--- Test 5: Descente valide a 16h30 ---")
res5 = process_scan("Ag1", override_date="2026-11-09", override_time="16:30:00")
print("Status:", res5["status"])
assert res5["status"] == "SUCCESS_DESCENTE"

print("\n--- Test 6: Retard (08:15) ---")
res6 = process_scan("Ag2", override_date="2026-11-09", override_time="08:15:00")
print("Status:", res6["status"], "| Retard:", res6["minutes_retard"], "min")
assert res6["statut_arrivee"] == "RETARD"
assert res6["minutes_retard"] == 45

print("\n--- Test 7: Hors delai (09:40) ---")
res7 = process_scan("Ag3", override_date="2026-11-09", override_time="09:40:00")
print("Status:", res7["status"])
assert res7["statut_arrivee"] == "HORS_DELAI"

print("\n--- Test 8: Securite - Descente sans arrivee le matin (16h15) ---")
res8 = process_scan("Ag4", override_date="2026-11-09", override_time="16:15:00")
print("Status:", res8["status"])
assert res8["status"] == "ANOMALIE_SECURITE"
assert res8["security_alert"] is True

print("\n--- Test 9: Dashboard verification ---")
dash = get_daily_dashboard("2026-11-09")
print("KPIs:", dash["kpis"])
assert dash["kpis"]["nb_a_l_heure"] == 1
assert dash["kpis"]["nb_retard"] == 1
assert dash["kpis"]["nb_hors_delai"] == 1
assert dash["kpis"]["nb_descentes"] == 2
assert dash["kpis"]["nb_sans_arrivee"] == 1
print("\n>>> ALL 9 CORE LOGIC TESTS PASSED WITH 100% SUCCESS! <<<")
