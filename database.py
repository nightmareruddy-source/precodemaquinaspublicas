import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "pm_publicas.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS maquinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        source_url TEXT,
        source_document_url TEXT,
        item_category TEXT,
        item_name TEXT,
        organ_name TEXT,
        municipality TEXT,
        supplier_name TEXT,
        contract_type TEXT,
        process_number TEXT,
        ata_number TEXT,
        purchase_year INTEGER,
        amount_brl REAL,
        validity_start TEXT,
        validity_end TEXT,
        status TEXT,
        raw_excerpt TEXT
    )
    """)

    conn.commit()
    conn.close()
