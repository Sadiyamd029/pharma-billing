
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

    # Medicines table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        batch TEXT,
        expiry TEXT,
        stock INTEGER
    )
    """)

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


# 🔐 CREATE USER (HASHED PASSWORD)
def create_user(username, password):
    hashed = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
    conn.commit()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()
    except:
        pass

    conn.close()


# 🔐 CHECK USER LOGIN
def check_user(username, password):
    cur.execute("SELECT password FROM users WHERE username=%s", (username,))
    result = cur.fetchone()

    if result:
        return check_password_hash(result[0], password)
    return False


# 📦 STOCK FUNCTIONS
def add_medicine(name, batch, expiry, stock):
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO medicines (name, batch, expiry, stock) VALUES (?, ?, ?, ?)",
        (name, batch, expiry, stock)
    )

    conn.commit()
    conn.close()


def reduce_stock(name, batch, qty):
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute(
        "UPDATE medicines SET stock = stock - ? WHERE name=? AND batch=?",
        (qty, name, batch)
    )

    conn.commit()
    conn.close()


def get_all_medicines():
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute("SELECT name, batch, expiry, stock FROM medicines")
    data = cur.fetchall()

    conn.close()
    return data


def get_alerts():
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM medicines WHERE stock < 10")
    low_stock = cur.fetchall()

    cur.execute("""
        SELECT * FROM medicines
        WHERE date(expiry) <= date('now', '+30 days')
    """)
    expiry_soon = cur.fetchall()

    conn.close()

import sqlite3
import bcrypt

def init_db():
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    # Medicines table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        batch TEXT,
        expiry TEXT,
        stock INTEGER
    )
    """)

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


# 🔐 CREATE USER (HASHED PASSWORD)
def create_user(username, password):
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()
    except:
        pass

    conn.close()


# 🔐 CHECK USER LOGIN
def check_user(username, password):
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    user = cur.fetchone()

    conn.close()

    if user:
        return bcrypt.checkpw(password.encode(), user[0])

    return False


# 📦 STOCK FUNCTIONS
def add_medicine(name, batch, expiry, stock):
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO medicines (name, batch, expiry, stock) VALUES (?, ?, ?, ?)",
        (name, batch, expiry, stock)
    )

    conn.commit()
    conn.close()


def reduce_stock(name, batch, qty):
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute(
        "UPDATE medicines SET stock = stock - ? WHERE name=? AND batch=?",
        (qty, name, batch)
    )

    conn.commit()
    conn.close()


def get_all_medicines():
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute("SELECT name, batch, expiry, stock FROM medicines")
    data = cur.fetchall()

    conn.close()
    return data


def get_alerts():
    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM medicines WHERE stock < 10")
    low_stock = cur.fetchall()

    cur.execute("""
        SELECT * FROM medicines
        WHERE date(expiry) <= date('now', '+30 days')
    """)
    expiry_soon = cur.fetchall()

    conn.close()
    
    return low_stock, expiry_soon