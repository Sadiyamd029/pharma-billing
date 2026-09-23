from flask import Flask, render_template, request, jsonify, redirect
from db import get_all_medicines, get_alerts

app = Flask(__name__)

# CHART DATA
@app.route("/chart_data")
def chart_data():
    medicines = get_all_medicines()

    labels = [m[0] for m in medicines]
    stock = [m[3] for m in medicines]

    return jsonify({
        "labels": labels,
        "stock": stock
    })

# HOME
@app.route('/')
def home():
    return render_template('index.html')

# BILLING
@app.route('/billing')
def billing():
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

            items.append({
                "name": names[i],
                "batch": batch[i],
                "qty": q,
                "amount": item_total
            })
        except:
            continue

    return render_template('invoice.html', items=items, total=total)

# LOGOUT
@app.route('/logout')
def logout():
    return redirect('/')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    medicines = get_all_medicines()

    total_medicines = len(medicines)
    total_stock = sum([m[3] for m in medicines]) if medicines else 0

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

    if request.method == "POST":
        add_medicine(
            request.form.get("name"),
            request.form.get("batch"),
            request.form.get("expiry"),
            int(request.form.get("stock"))
        )

    medicines = get_all_medicines()
    return render_template('add_stock.html', medicines=medicines)

# EDIT
@app.route("/edit/<name>/<batch>", methods=["GET", "POST"])
def edit(name, batch):
    import sqlite3

    if request.method == "POST":
        new_stock = request.form.get("stock")

        conn = sqlite3.connect("pharma.db")
        cur = conn.cursor()

        cur.execute("""
            UPDATE medicines
            SET stock = ?
            WHERE name = ? AND batch = ?
        """, (new_stock, name, batch))

        conn.commit()
        conn.close()

        return redirect("/add_stock")

    return render_template("edit.html", name=name, batch=batch)

# DELETE
@app.route("/delete/<name>/<batch>")
def delete(name, batch):
    import sqlite3

    conn = sqlite3.connect("pharma.db")
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM medicines
        WHERE name = ? AND batch = ?
    """, (name, batch))

    conn.commit()
    conn.close()

    return redirect("/add_stock")

# ALERTS
@app.route('/alerts')
def alerts():
    low_stock, expiry_soon = get_alerts()

    return render_template(
        'alerts.html',
        low_stock=low_stock,
        expiry_soon=expiry_soon
    )

if __name__ == "__main__":
    app.run(debug=True)