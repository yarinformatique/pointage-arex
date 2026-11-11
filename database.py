import sqlite3
import os
import json
import datetime
import re

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pointage_arex.db")

def get_database_url():
    return (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("SUPABASE_DB_URL")
        or ""
    ).strip()

def is_postgres():
    return bool(get_database_url())

# ---------------------------------------------------------------------------
# POSTGRES COMPATIBILITY WRAPPER (FOR SUPABASE / VERCEL)
# ---------------------------------------------------------------------------
class PostgresCursorWrapper:
    def __init__(self, pg_cursor):
        self.cursor = pg_cursor
        self.lastrowid = None

    def execute(self, sql, params=None):
        sql_pg = self._translate_sql(sql)
        try:
            if params:
                self.cursor.execute(sql_pg, tuple(params))
            else:
                self.cursor.execute(sql_pg)
            if "INSERT" in sql.upper():
                try:
                    self.cursor.execute("SELECT LASTVAL();")
                    row = self.cursor.fetchone()
                    if row:
                        self.lastrowid = row[0]
                except Exception:
                    self.lastrowid = None
        except Exception as e:
            raise e
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    def _translate_sql(self, sql):
        upper = sql.upper()
        # Primary key
        sql = re.sub(r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
        # INSERT OR IGNORE INTO
        if "INSERT OR IGNORE INTO" in upper:
            sql = re.sub(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", sql, flags=re.IGNORECASE)
            if "ON CONFLICT" not in sql.upper():
                sql = sql.rstrip(";").strip() + " ON CONFLICT DO NOTHING"
        # INSERT OR REPLACE INTO
        if "INSERT OR REPLACE INTO" in upper:
            sql = re.sub(r"\bINSERT\s+OR\s+REPLACE\s+INTO\b", "INSERT INTO", sql, flags=re.IGNORECASE)
            if "ON CONFLICT" not in sql.upper():
                sql = sql.rstrip(";").strip() + " ON CONFLICT DO NOTHING"
        # Replace ? with %s
        sql = sql.replace("?", "%s")
        return sql

    def close(self):
        self.cursor.close()

class PostgresConnectionWrapper:
    def __init__(self, pg_conn):
        self.conn = pg_conn

    def cursor(self):
        import psycopg2.extras
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return PostgresCursorWrapper(cur)

    def execute(self, sql, params=None):
        cur = self.cursor()
        return cur.execute(sql, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_connection():
    db_url = get_database_url()
    if db_url:
        try:
            import psycopg2
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            if "sslmode=" not in db_url and "localhost" not in db_url and "127.0.0.1" not in db_url:
                delimiter = "&" if "?" in db_url else "?"
                db_url = f"{db_url}{delimiter}sslmode=require"
            pg_conn = psycopg2.connect(db_url, connect_timeout=10)
            pg_conn.autocommit = True
            return PostgresConnectionWrapper(pg_conn)
        except Exception as e:
            print(f"[Supabase Fallback -> SQLite] {e}")

    # Fallback to local SQLite
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Clean agent roster
RAW_AGENTS_SEED = [
    ("Ag1", "BAZIÉ", "Laurent", "Ag1 BAZIÉ LAURENT", "Ouvrier"),
    ("Ag2", "LENGA", "Lambert", "Ag2 LENGA LAMBERT", "Ouvrier"),
    ("Ag3", "ZONGO", "Antoine", "Ag3 ZONGO ANTOINE", "Ouvrier"),
    ("Ag4", "NENKELSE", "Bertrand", "Ag4 NENKELSE BERTRAND", "Ouvrier"),
    ("Ag5", "KONATÉ", "Henry", "Ag5 KONATÉ HENRY", "Ouvrier"),
    ("Ag6", "DEMBÉLÉ", "Bienvenu", "Ag6 DEMBÉLÉ BIENVENU", "Ouvrier"),
    ("Ag7", "ZAGRÉ", "Franck", "Ag7 ZAGRÉ FRANCK", "Ouvrier"),
    ("Ag8", "DEMBÉLÉ", "Issouf", "Ag8 DEMBÉLÉ ISSOUF", "Ouvrier"),
    ("Ag9", "SANOU", "Bernard", "Ag9 SANOU BERNARD", "Ouvrier"),
    ("Ag10", "BAZIÉ", "Roland", "Ag10 BAZIÉ ROLAND", "Ouvrier"),
    ("Ag11", "BAZIÉ", "A. Rahim", "Ag11 BAZIÉ A.RAHIM", "Ouvrier"),
    ("Ag12", "BATIENE", "S.M.S.G. Juldas", "Ag12 BATIENE S.M.S.G.JULDAS", "Ouvrier"),
    ("Ag13", "KONAN", "Kouame-Alphonse", "Ag13 KONAN KOUAME-ALPHONSE", "Ouvrier"),
    ("Ag14", "TANO", "N'Gessan", "Ag14 TANO N'GESSAN", "Ouvrier"),
    ("Ag15", "SANOU", "Zephirin", "Ag15 SANOU ZEPHIRIN", "Ouvrier"),
    ("Ag16", "OUATTARA", "Hamidou", "Ag16 OUATTARA Hamidou", "Ouvrier"),
    ("Ag17", "ZIE", "Honoré", "Ag17 ZIE HONORÉ", "Ouvrier"),
    ("Ag18", "NIAMBA", "Simon", "Ag18 NIAMBA SIMON", "Ouvrier"),
    ("Ag19", "ZONGO", "S-Mohamadi", "Ag19 ZONGO S-MOHAMADI", "Ouvrier"),
    ("Ag20", "TRAORE", "Bayoa", "Ag20 TRAORE BAYOA", "Ouvrier"),
    ("Ag21", "NEYA", "Belibi-Denis", "Ag21 NEYA BELIBI-DENIS", "Ouvrier"),
    ("Ag22", "RABO", "Mohamed-Lamine", "Ag22 RABO MOHAMED-LAMINE", "Ouvrier"),
    ("Ag23", "SANOU", "Alain", "Ag23 SANOU ALAIN", "Ouvrier"),
    ("Ag24", "SANOU", "Aboubacar", "Ag24 SANOU ABOUBACAR", "Ouvrier"),
    ("Ag25", "DAYO", "Vincent", "Ag25 DAYO Vincent", "Ouvrier"),
    ("Ag26", "DOYÉ", "Toumbé", "Ag26 DOYÉ Toumbé", "Ouvrier"),
    ("Ag27", "DOYÉ", "Dapoba", "Ag27 DOYÉ Dapoba", "Ouvrier"),
    ("Ag28", "DOYÉ", "Romuald", "Ag28 DOYÉ Romuald", "Ouvrier"),
    ("Ag29", "WOIN", "Madou", "Ag29 WOIN Madou", "Ouvrier"),
    ("Ag30", "KONDÉ", "Denis", "Ag30 KONDÉ Denis", "Ouvrier"),
    ("Ag31", "ZERBO", "Joseph", "Ag31 ZERBO Joseph", "Ouvrier"),
    ("Ag32", "DAYO", "Émile", "Ag32 DAYO Émile", "Ouvrier"),
    ("Ag33", "SAMA", "Victor", "Ag33 SAMA Victor", "Ouvrier"),
    ("Ag34", "DRABO", "Noufou", "Ag34 DRABO Noufou", "Ouvrier"),
    ("Ag35", "SARY", "Yacouba", "Ag35 SARY Yacouba", "Ouvrier"),
    ("Ag36", "SAWADOGO", "Arouna", "Ag36 SAWADOGO Arouna", "Ouvrier"),
    ("Ag37", "TRAORÉ", "Abdoulaye", "Ag37 TRAORÉ Abdoulaye", "Ouvrier"),
    ("Ag38", "DOUBARE", "Ibrahim", "Ag38 DOUBARE Ibrahim", "Ouvrier"),
    ("Ag39", "MOUSIANE", "Grégoire", "Ag39 MOUSIANE Grégoire", "Ouvrier"),
    ("Ag40", "DJIRÉ", "Adama", "Ag40 DJIRÉ Adama", "Ouvrier"),
    ("Ag41", "KOUADIO", "M.-N.-Roland", "Ag41 KOUADIO M.-N.-Roland", "Ouvrier"),
    ("Ag42", "OUEDRAOGO", "Pierre", "Ag42 OUEDRAOGO Pierre", "Ouvrier"),
    ("Ag43", "PARÉ", "Ibrahim", "Ag43 PARÉ Ibrahim", "Chef Maçon"),
    ("Ag44", "IRIÉ", "Elvis", "Ag44 IRIÉ Elvis", "Ingénieur"),
    ("Ag45", "KINDA", "W. J. Mario", "Ag45 KINDA W. J. Mario", "Chauffeur"),
    ("Ag46", "OUEDRAOGO", "Ousseni", "Ag46 OUEDRAOGO Ousseni", "Ferrailleur"),
    ("Ag47", "SAWADOGO", "Adama", "Ag47 SAWADOGO Adama", "Chef Ferrailleur"),
    ("Ag48", "BORO", "Adama", "Ag48 BORO Adama", "Menuisier"),
    ("Ag49", "SOSSO", "Serge", "Ag49 SOSSO Serge", "Menuisier"),
    ("Ag50", "KABORÉ", "Michel", "Ag50 KABORÉ Michel", "HSSE"),
    ("Ag51", "TOU", "Aboubacar", "Ag51 TOU Aboubacar", "Magasinier"),
    ("Ag52", "SERY", "Daouda", "Ag52 SERY Daouda", "Chef Menuisier"),
    ("Ag53", "PALENFO", "K.M. Yazid", "Ag53 PALENFO K.M. Yazid", "Conducteur"),
    ("Ag54", "BAMBIO", "Bosco", "Ag54 BAMBIO Bosco", "Ouvrier"),
    ("Ag55", "BAMBIO", "Begnamou", "Ag55 BAMBIO Begnamou", "Ouvrier"),
    ("Ag56", "SOLANA", "Francis", "Ag56 SOLANA Francis", "Menuisier"),
    ("Ag57", "SIDIBÉ", "Ousmane", "Ag57 SIDIBÉ Ousmane", "Menuisier"),
    ("Ag58", "SORY", "Jules", "Ag58 SORY Jules", "Menuisier"),
    ("Ag59", "BAZIE", "Aboubacar", "Ag59 BAZIE Aboubacar", "Menuisier"),
    ("Ag60", "SIRIBIE", "Ibrahim", "Ag60 SIRIBIE Ibrahim", "Menuisier"),
    ("Ag61", "SOMANDA", "Yacouba", "Ag61 SOMANDA Yacouba", "Briquetier"),
    ("Ag62", "KAMBOU", "Kévin", "Ag62 KAMBOU Kévin", "Bétonnier"),
    ("Ag63", "DAO", "Karim", "Ag63 DAO Karim", "Bétonnier"),
    ("Ag64", "ZIDA", "Alidou", "Ag64 ZIDA Alidou", "Bétonnier"),
    ("Ag65", "BONKOUNGOU", "Lookman", "Ag65 BONKOUNGOU Lookman", "Ferrailleur"),
    ("Ag66", "SAWADOGO", "Zakaria", "Ag66 SAWADOGO Zakaria", "Ferrailleur"),
    ("Ag67", "OURA", "Dieudonné", "Ag67 OURA Dieudonné", "Ouvrier"),
    ("Ag68", "TRAORE", "A. Fatao", "Ag68 TRAORE A. Fatao", "Ouvrier")
]

GOOGLE_FORM_BASE = "https://docs.google.com/forms/d/e/1FAIpQLSdoQrCfoN8x5TxD2rgJJwzlw_oWUJmKuaCHDm00tYADJH-98w/formResponse?entry.1849590193="

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Table agents
    c.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricule TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        identite TEXT NOT NULL,
        fonction TEXT DEFAULT 'Ouvrier',
        telephone TEXT DEFAULT '',
        google_form_url TEXT DEFAULT '',
        actif INTEGER DEFAULT 1,
        date_creation TEXT
    )
    """)

    # Table pointages
    c.execute("""
    CREATE TABLE IF NOT EXISTS pointages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        heure_arrivee TEXT,
        statut_arrivee TEXT,
        minutes_retard INTEGER DEFAULT 0,
        heure_descente TEXT,
        statut_descente TEXT,
        temps_travail_minutes INTEGER DEFAULT 0,
        note TEXT DEFAULT '',
        mode_scan_arrivee TEXT,
        mode_scan_descente TEXT,
        created_at TEXT,
        updated_at TEXT,
        UNIQUE(agent_id, date)
    )
    """)

    # Table anomalies
    c.execute("""
    CREATE TABLE IF NOT EXISTS anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER,
        date TEXT NOT NULL,
        heure TEXT NOT NULL,
        type TEXT NOT NULL,
        details TEXT,
        resolu INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # Table parametres
    c.execute("""
    CREATE TABLE IF NOT EXISTS parametres (
        cle TEXT PRIMARY KEY,
        valeur TEXT
    )
    """)

    # Default settings
    default_params = {
        "nom_entreprise": "POINTAGE AREX",
        "sous_titre": "Génie Civil & BTP - Bobo-Dioulasso, Burkina Faso",
        "heure_arrivee_debut": "06:00",
        "heure_arrivee_limite": "07:30",
        "heure_retard_limite": "09:00",
        "heure_descente_debut": "16:00",
        "antirebond_secondes": "60",
        "code_superviseur": "1234",
        "auto_absent_apres_9h": "1"
    }
    for k, v in default_params.items():
        c.execute("INSERT OR IGNORE INTO parametres (cle, valeur) VALUES (?, ?)", (k, v))

    # Seed agents if empty
    c.execute("SELECT COUNT(*) FROM agents")
    count_row = c.fetchone()
    count = list(count_row.values())[0] if isinstance(count_row, dict) else count_row[0]
    if count == 0:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for mlle, nom, prenom, identite, fonction in RAW_AGENTS_SEED:
            url_encoded_id = identite.replace(' ', '+')
            gform_url = f"{GOOGLE_FORM_BASE}{url_encoded_id}"
            c.execute("""
                INSERT INTO agents (matricule, nom, prenom, identite, fonction, google_form_url, actif, date_creation)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """, (mlle, nom, prenom, identite, fonction, gform_url, now_str))
        conn.commit()
        print(f"[OK] Database seeded with {len(RAW_AGENTS_SEED)} agents.")
    else:
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
