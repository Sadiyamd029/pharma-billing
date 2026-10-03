import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# expiry is always read back as text, so a bad/corrupted date can never
# crash Python with a type error — we just get a string to safely parse.
MED_COLS = """id, name, mfr, hsn, pack, batch, purchase_price,
              rate, mrp, gst, stock, expiry::text AS expiry"""


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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS parties(
        id SERIAL PRIMARY KEY,
        name TEXT,
        address TEXT,
        gstin TEXT,
        phone TEXT,
        state TEXT,
        d20b TEXT,
        d21b TEXT
    )
    """)

    conn.commit()

    # Clear any corrupted expiry year (more than 4 digits, e.g. "72027")
    # left over from earlier test entries, so it can never crash a query.
    try:
        cur.execute("""
            UPDATE medicines SET expiry = NULL
            WHERE expiry IS NOT NULL
              AND LENGTH(SPLIT_PART(expiry::text, '-', 1)) > 4
        """)
        conn.commit()
    except Exception:
        conn.rollback()

    conn.close()


def create_bill():
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
    cur.execute(f"SELECT {MED_COLS} FROM medicines ORDER BY name")
    data = cur.fetchall()
    conn.close()
    return data


def get_medicine(name, batch):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT {MED_COLS} FROM medicines WHERE name = %s AND batch = %s", (name, batch))
    data = cur.fetchone()
    conn.close()
    return data


def update_medicine(old_name, old_batch, name, mfr, hsn, pack, batch, expiry,
                     purchase_price, rate, mrp, gst, stock):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE medicines
        SET name=%s, mfr=%s, hsn=%s, pack=%s, batch=%s, expiry=%s,
            purchase_price=%s, rate=%s, mrp=%s, gst=%s, stock=%s
        WHERE name=%s AND batch=%s
    """, (name, mfr, hsn, pack, batch, expiry, purchase_price, rate, mrp, gst, stock,
          old_name, old_batch))
    conn.commit()
    conn.close()


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

    cur.execute(f"SELECT {MED_COLS} FROM medicines WHERE stock < 5")
    low_stock = cur.fetchall()

    cur.execute(f"SELECT {MED_COLS} FROM medicines WHERE expiry IS NOT NULL")
    all_with_expiry = cur.fetchall()

    conn.close()

    expiry_soon = []
    cutoff = datetime.now().date() + timedelta(days=30)

    for m in all_with_expiry:
        s = (m['expiry'] or '').strip()[:10]
        try:
            exp_date = datetime.strptime(s, '%Y-%m-%d').date()
        except ValueError:
            continue  # skip garbage dates instead of crashing

        if exp_date <= cutoff:
            expiry_soon.append(m)

    return low_stock, expiry_soon


def add_party(name, address, gstin, phone, state, d20b, d21b):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO parties (name, address, gstin, phone, state, d20b, d21b)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (name, address, gstin, phone, state, d20b, d21b))
    conn.commit()
    conn.close()


def get_all_parties():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM parties ORDER BY name")
    data = cur.fetchall()
    conn.close()
    return data


def delete_party(party_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM parties WHERE id = %s", (party_id,))
    conn.commit()
    conn.close()