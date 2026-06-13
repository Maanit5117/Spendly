import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'spendly.db'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    db = get_db()
    with db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """)
    db.close()

def seed_db():
    db = get_db()
    
    # Check if users table already contains data
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users LIMIT 1;")
    user_exists = cursor.fetchone()
    if user_exists:
        db.close()
        return
        
    # Seed user
    password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);",
        ("Demo User", "demo@spendly.com", password_hash)
    )
    user_id = cursor.lastrowid
    
    # Seed 8 expenses
    expenses_data = [
        (user_id, 15.50, "Food", "2026-06-01", "Lunch at cafe"),
        (user_id, 5.75, "Transport", "2026-06-02", "Bus fare"),
        (user_id, 120.00, "Bills", "2026-06-05", "Electricity bill"),
        (user_id, 45.00, "Health", "2026-06-07", "Pharmacy"),
        (user_id, 22.00, "Entertainment", "2026-06-09", "Movie ticket"),
        (user_id, 65.50, "Shopping", "2026-06-10", "New shoes"),
        (user_id, 10.00, "Other", "2026-06-12", "Notebook"),
        (user_id, 32.40, "Food", "2026-06-13", "Groceries")
    ]
    
    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?);",
        expenses_data
    )
    db.commit()
    db.close()


def create_user(name, email, password):
    """
    Hashes the password with werkzeug, inserts a row into users,
    and returns the new user's id. Raises sqlite3.IntegrityError
    if the email is already taken.
    """
    password_hash = generate_password_hash(password)
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);",
            (name, email, password_hash)
        )
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()


def get_user_by_email(email):
    """
    Retrieves a user row by email. Returns a dict-like sqlite3.Row object
    if found, or None if not found.
    """
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?;", (email,))
        return cursor.fetchone()
    finally:
        db.close()


