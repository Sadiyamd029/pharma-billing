from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import get_all_medicines, get_alerts, init_db

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
# INVOICE
@app.route('/invoice', methods=['POST'])
def invoice():
    names   = request.form.getlist('name')
    mfrs    = request.form.getlist('mfr')
    hsns    = request.form.getlist('hsn')
    packs   = request.form.getlist('pack')
    batches = request.form.getlist('batch')
    expiry  = request.form.getlist('expiry')
    mrps    = request.form.getlist('mrp')
    qtys    = request.form.getlist('qty')
    frees   = request.form.getlist('free')
    rates   = request.form.getlist('rate')
    discs   = request.form.getlist('disc')
    gsts    = request.form.getlist('gst')

    party = request.form.get('party', '')

    items = []
    total_taxable = 0
    total_cgst = 0
    total_sgst = 0
    net_amount = 0

    for i in range(len(names)):
        if not names[i]:
            continue
        try:
            qty  = float(qtys[i]) if qtys[i] else 0
            rate = float(rates[i]) if rates[i] else 0
            free = float(frees[i]) if frees[i] else 0
            disc = float(discs[i]) if discs[i] else 0
            gst  = float(gsts[i]) if gsts[i] else 0
            mrp  = float(mrps[i]) if mrps[i] else 0
        except ValueError:
            continue

        gross = qty * rate
        disc_amt = gross * disc / 100
        taxable = gross - disc_amt

        cgst_rate = gst / 2
        sgst_rate = gst / 2
        cgst_amt = taxable * cgst_rate / 100
        sgst_amt = taxable * sgst_rate / 100

        line_total = taxable + cgst_amt + sgst_amt

        total_taxable += taxable
        total_cgst += cgst_amt
        total_sgst += sgst_amt
        net_amount += line_total

        items.append({
            "name": names[i],
            "mfr": mfrs[i] if i < len(mfrs) else "",
            "hsn": hsns[i] if i < len(hsns) else "",
            "pack": packs[i] if i < len(packs) else "",
            "batch": batches[i],
            "expiry": expiry[i] if i < len(expiry) else "",
            "mrp": round(mrp, 2),
            "qty": qty,
            "free": free,
            "rate": rate,
            "disc": disc,
            "taxable": round(taxable, 2),
            "gst_rate": gst,
            "cgst_rate": cgst_rate,
            "cgst_amt": round(cgst_amt, 2),
            "sgst_rate": sgst_rate,
            "sgst_amt": round(sgst_amt, 2),
            "amount": round(line_total, 2),
        })

    tax_summary = {}
    for it in items:
        r = it["gst_rate"]
        if r not in tax_summary:
            tax_summary[r] = {"rate": r, "taxable": 0, "cgst": 0, "sgst": 0}
        tax_summary[r]["taxable"] += it["taxable"]
        tax_summary[r]["cgst"] += it["cgst_amt"]
        tax_summary[r]["sgst"] += it["sgst_amt"]

    return render_template(
        'invoice.html',
        items=items,
        party=party,
        total_taxable=round(total_taxable, 2),
        total_cgst=round(total_cgst, 2),
        total_sgst=round(total_sgst, 2),
        total=round(net_amount, 2),
        tax_summary=list(tax_summary.values()),
    )
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
    if 'user' not in session:
        return redirect('/login')

    low_stock, expiry_soon = get_alerts()
    return render_template('alerts.html', low_stock=low_stock, expiry_soon=expiry_soon)

if __name__ == "__main__":
    app.run(debug=True)