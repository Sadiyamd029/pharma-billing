import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

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

    for col, coltype in [
        ("mfr", "TEXT"),
        ("hsn", "TEXT"),
        ("pack", "TEXT"),
        ("purchase_price", "REAL"),
        ("rate", "REAL"),
        ("mrp", "REAL"),
        ("gst", "REAL"),
    ]:
        cur.execute(f"ALTER TABLE medicines ADD COLUMN IF NOT EXISTS {col} {coltype}")

    # Bill numbering — every generated invoice gets a permanent, incrementing number
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def create_bill():
    """Creates a new bill record and returns its number (the SERIAL id)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO bills DEFAULT VALUES RETURNING id")
    bill_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return bill_id


def add_medicine(name, mfr, hsn, pack, batch, expiry, purchase_price, rate, mrp, gst, stock):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO medicines
        (name, mfr, hsn, pack, batch, expiry, purchase_price, rate, mrp, gst, stock)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (name, mfr, hsn, pack, batch, expiry, purchase_price, rate, mrp, gst, stock))

    conn.commit()
    conn.close()


def get_all_medicines():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM medicines ORDER BY name")
    data = cur.fetchall()
    conn.close()
    return data


def reduce_stock(name, batch, qty):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE medicines
        SET stock = GREATEST(stock - %s, 0)
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