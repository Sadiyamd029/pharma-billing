import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

# 🔗 CONNECT TO POSTGRES (FIXED FOR RENDER)
DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()


# 🧠 INIT DB
def init_db():

    # Medicines table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id SERIAL PRIMARY KEY,
        name TEXT,
        batch TEXT,
        expiry DATE,
        stock INTEGER
    )
    """)

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    conn.commit()


# 🔐 CREATE USER (SAFE)
def create_user(username, password, role="admin"):
    hashed = generate_password_hash(password)

    try:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed, role)
        )
        conn.commit()
    except Exception as e:
        # Ignore duplicate user error
        conn.rollback()


# 🔐 CHECK LOGIN (SAFE)
def check_user(username, password):
    cur.execute("SELECT password, role FROM users WHERE username=%s", (username,))
    result = cur.fetchone()

    if result:
        stored_password, role = result

        if check_password_hash(stored_password, password):
            return role

    return None


# 📦 ADD MEDICINE
def add_medicine(name, batch, expiry, stock):
    try:
        cur.execute(
            "INSERT INTO medicines (name, batch, expiry, stock) VALUES (%s, %s, %s, %s)",
            (name, batch, expiry, stock)
        )
        conn.commit()
    except:
        conn.rollback()


# 📉 REDUCE STOCK
def reduce_stock(name, batch, qty):
    try:
        cur.execute(
            "UPDATE medicines SET stock = stock - %s WHERE name=%s AND batch=%s",
            (qty, name, batch)
        )
        conn.commit()
    except:
        conn.rollback()


# 📋 GET ALL MEDICINES
def get_all_medicines():
    cur.execute("SELECT name, batch, expiry, stock FROM medicines")
    return cur.fetchall()


# ⚠️ ALERTS
def get_alerts():

    # Low stock
    cur.execute("SELECT * FROM medicines WHERE stock < 10")
    low_stock = cur.fetchall()

    # Expiry soon
    cur.execute("""
        SELECT * FROM medicines
        WHERE expiry <= CURRENT_DATE + INTERVAL '30 days'
    """)
    expiry_soon = cur.fetchall()

    return low_stock, expiry_soon


# ✏️ UPDATE MEDICINE
def update_medicine(name, batch, stock):
    try:
        cur.execute(
            "UPDATE medicines SET stock=%s WHERE name=%s AND batch=%s",
            (stock, name, batch)
        )
        conn.commit()
    except:
        conn.rollback()


# ❌ DELETE MEDICINE
def delete_medicine(name, batch):
    try:
        cur.execute(
            "DELETE FROM medicines WHERE name=%s AND batch=%s",
            (name, batch)
        )
        conn.commit()
    except:
        conn.rollback()