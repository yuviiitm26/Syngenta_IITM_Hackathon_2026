import sqlite3

DB_PROD = "syngenta_prod.db"
DB_CLOUD = "syngenta_prod.db" # Defaulting to the same for now

def get_db_connection(db_path=DB_PROD):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
