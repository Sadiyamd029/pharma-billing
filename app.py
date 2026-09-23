from flask import Flask, render_template, request, jsonify
from db import get_all_medicines   # ✅ import this

app = Flask(__name__)

# 🔥 CHART DATA
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
                "amount": item_total   # ✅ fixed key name
            })
        except:
            continue

    return render_template('invoice.html', items=items, total=total)


# DASHBOARD (fixed)
@app.route('/dashboard')
def dashboard():
    medicines = get_all_medicines()

    total_medicines = len(medicines)
    total_stock = sum([m[3] for m in medicines]) if medicines else 0

    return render_template(
        'dashboard.html',
        total_medicines=total_medicines,
        total_stock=total_stock,
        low_stock=0,        # temporary
        expiry_soon=0       # temporary
    )


# STOCK PAGE
@app.route('/add_stock')
def add_stock():
    medicines = get_all_medicines()
    return render_template('add_stock.html', medicines=medicines)


# ALERTS PAGE
@app.route('/alerts')
def alerts():
    return render_template('alerts.html', low_stock=[], expiry_soon=[])


if __name__ == '__main__':
    app.run(debug=True)