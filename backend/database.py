import sqlite3
import os
from passlib.context import CryptContext

DB_PATH = "syngenta_prod.db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_password_hash(password):
    return pwd_context.hash(password)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            rep_id TEXT,
            role TEXT DEFAULT 'rep'
        )
    """)
    
    # Check if a default user exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # Create a default admin user
        # Password is 'syngenta2026'
        hashed_pw = get_password_hash("syngenta2026")
        cursor.execute(
            "INSERT INTO users (username, hashed_password, full_name, role) VALUES (?, ?, ?, ?)",
            ("admin", hashed_pw, "Syngenta Admin", "admin")
        )
        print("✅ Default user 'admin' created with password 'syngenta2026'")
    
    # Create a test rep user
    cursor.execute("SELECT * FROM users WHERE username = 'rep1'")
    if not cursor.fetchone():
        hashed_pw = get_password_hash("syngenta2026")
        cursor.execute(
            "INSERT INTO users (username, hashed_password, full_name, rep_id, role) VALUES (?, ?, ?, ?, ?)",
            ("rep1", hashed_pw, "Sales Rep 1", "REP_001", "rep")
        )
        print("✅ Test user 'rep1' created with password 'syngenta2026'")

    conn.commit()
    conn.close()
    print("✓ Database initialized successfully.")

if __name__ == "__main__":
    init_db()
