from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("pharma.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines(
        name TEXT,
        batch TEXT,
        expiry TEXT,
        stock INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid login"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html")


# ---------------- BILLING ----------------
@app.route("/billing", methods=["GET", "POST"])
def billing():
    if "user" not in session:
        return redirect("/login")

    items = []
    total = 0

    if request.method == "POST":
        names = request.form.getlist("name")
        batches = request.form.getlist("batch")
        qtys = request.form.getlist("qty")
        rates = request.form.getlist("rate")

        for i in range(len(names)):
            try:
                qty = float(qtys[i])
                rate = float(rates[i])
                amount = qty * rate
                total += amount

                items.append({
                    "name": names[i],
                    "batch": batches[i],
                    "qty": qty,
                    "amount": amount
                })
            except:
                pass

    return render_template("index.html", items=items, total=total)


# ---------------- STOCK ----------------
@app.route("/add_stock", methods=["GET", "POST"])
def add_stock():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        batch = request.form.get("batch")
        expiry = request.form.get("expiry")
        stock = request.form.get("stock")

        cur.execute("INSERT INTO medicines VALUES (?, ?, ?, ?)",
                    (name, batch, expiry, stock))
        conn.commit()

    cur.execute("SELECT * FROM medicines")
    medicines = cur.fetchall()
    conn.close()

    return render_template("stock.html", medicines=medicines)


# ---------------- ALERTS ----------------
@app.route("/alerts")
def alerts():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM medicines WHERE stock < 5")
    low_stock = cur.fetchall()

    conn.close()

    return render_template("alerts.html", medicines=low_stock)


if __name__ == "__main__":
    app.run(debug=True)