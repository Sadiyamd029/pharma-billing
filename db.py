import sqlite3

# ---------------- CONNECT ----------------
def get_db():
    conn = sqlite3.connect("pharma.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DB ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        batch TEXT,
        expiry TEXT,
        stock INTEGER
    )
    """)

    conn.commit()
    conn.close()


# ---------------- ADD MEDICINE ----------------
def add_medicine(name, batch, expiry, stock):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO medicines (name, batch, expiry, stock) VALUES (?, ?, ?, ?)",
        (name, batch, expiry, stock)
    )

    conn.commit()
    conn.close()


# ---------------- GET ALL ----------------
def get_all_medicines():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM medicines")
    data = cur.fetchall()

    conn.close()
    return data


# ---------------- REDUCE STOCK ----------------
def reduce_stock(name, batch, qty):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE medicines
        SET stock = stock - ?
        WHERE name = ? AND batch = ?
    """, (qty, name, batch))

    conn.commit()
    conn.close()


# ---------------- ALERTS ----------------
def get_alerts():
    conn = get_db()
    cur = conn.cursor()

    # low stock (<5)
    cur.execute("SELECT * FROM medicines WHERE stock < 5")
    low_stock = cur.fetchall()

    # expiry soon (simple version - you can improve later)
    cur.execute("SELECT * FROM medicines WHERE expiry != ''")
    expiry_soon = cur.fetchall()

    conn.close()

    return low_stock, expiry_soon


# ---------------- USER SYSTEM ----------------
def create_user(username, password):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
    except:
        pass

    conn.commit()
    conn.close()


def check_user(username, password):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM users
        WHERE username = ? AND password = ?
    """, (username, password))

    user = cur.fetchone()

    conn.close()
    return user is not None