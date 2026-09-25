import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Render sometimes hands out "postgres://" which newer psycopg2 rejects
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines(
        id SERIAL PRIMARY KEY,
        name TEXT,
        batch TEXT,
        expiry TEXT,
        stock INTEGER
    )
    """)

    conn.commit()
    conn.close()


def add_medicine(name, batch, expiry, stock):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO medicines (name, batch, expiry, stock) VALUES (%s, %s, %s, %s)",
        (name, batch, expiry, stock)
    )

    conn.commit()
    conn.close()


def get_all_medicines():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM medicines ORDER BY name")
    data = cur.fetchall()

    conn.close()
    return data  # each row supports m["name"], m["batch"], etc — same as before


def reduce_stock(name, batch, qty):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE medicines
        SET stock = stock - %s
        WHERE name = %s AND batch = %s
    """, (qty, name, batch))

    conn.commit()
    conn.close()


def get_alerts():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM medicines WHERE stock < 5")
    low_stock = cur.fetchall()

    cur.execute("""
        SELECT * FROM medicines
        WHERE expiry IS NOT NULL AND expiry != ''
        AND TO_DATE(expiry, 'YYYY-MM-DD') <= CURRENT_DATE + INTERVAL '30 days'
    """)
    expiry_soon = cur.fetchall()

    conn.close()
    return low_stock, expiry_soon