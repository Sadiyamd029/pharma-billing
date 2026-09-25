from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import get_all_medicines, get_alerts, init_db, get_db

app = Flask(__name__)
app.secret_key = "sa0206"

init_db()

# CHART DATA
@app.route("/chart_data")
def chart_data():
    medicines = get_all_medicines()
    labels = [m["name"] for m in medicines]
    stock = [m["stock"] for m in medicines]
    return jsonify({"labels": labels, "stock": stock})

# HOME
@app.route('/')
def home():
    return redirect('/login')

# BILLING
@app.route('/billing')
def billing():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

# INVOICE
@app.route('/invoice', methods=['POST'])
def invoice():
    items = []
    names = request.form.getlist('name')
    batch = request.form.getlist('batch')
    qty = request.form.getlist('qty')
    rate = request.form.getlist('rate')
    total = 0

    for i in range(len(names)):
        try:
            q = float(qty[i])
            r = float(rate[i])
            item_total = q * r
            total += item_total
            items.append({"name": names[i], "batch": batch[i], "qty": q, "amount": item_total})
        except:
            continue

    return render_template('invoice.html', items=items, total=total)

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('username')
        return redirect('/billing')
    return render_template('login.html')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    medicines = get_all_medicines()
    total_medicines = len(medicines)
    total_stock = sum([int(m["stock"]) for m in medicines]) if medicines else 0

    return render_template(
        'dashboard.html',
        total_medicines=total_medicines,
        total_stock=total_stock,
        low_stock=0,
        expiry_soon=0
    )

# STOCK PAGE
@app.route('/add_stock', methods=["GET", "POST"])
def add_stock():
    from db import add_medicine

    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":
        stock = request.form.get("stock")
        stock = int(stock) if stock else 0

        add_medicine(
            request.form.get("name"),
            request.form.get("batch"),
            request.form.get("expiry"),
            stock
        )

    medicines = get_all_medicines()
    return render_template('add_stock.html', medicines=medicines)

# EDIT
@app.route("/edit/<name>/<batch>", methods=["GET", "POST"])
def edit(name, batch):
    if request.method == "POST":
        new_stock = request.form.get("stock")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE medicines
            SET stock = %s
            WHERE name = %s AND batch = %s
        """, (new_stock, name, batch))
        conn.commit()
        conn.close()

        return redirect("/add_stock")

    return render_template("edit.html", name=name, batch=batch)

# DELETE
@app.route("/delete/<name>/<batch>")
def delete(name, batch):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM medicines
        WHERE name = %s AND batch = %s
    """, (name, batch))
    conn.commit()
    conn.close()

    return redirect("/add_stock")

# ALERTS
@app.route('/alerts')
def alerts():
    if 'user' not in session:
        return redirect('/login')

    low_stock, expiry_soon = get_alerts()
    return render_template('alerts.html', low_stock=low_stock, expiry_soon=expiry_soon)

if __name__ == "__main__":
    app.run(debug=True)