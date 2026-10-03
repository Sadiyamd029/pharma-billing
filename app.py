from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import (
    get_all_medicines, get_alerts, init_db, get_db, add_medicine, reduce_stock, create_bill,
    add_party, get_all_parties, delete_party, get_medicine, update_medicine
)
from datetime import date, datetime
import os

app = Flask(__name__)
app.secret_key = "sa0206"

init_db()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234")

SELLER_D20B = "WLF20B2025AP001258"
SELLER_D21B = "WLF21B2025AP001249"


def format_expiry(value):
    if not value:
        return ""
    if isinstance(value, (date, datetime)):
        return value.strftime('%m/%Y')
    s = str(value).strip()
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').strftime('%m/%Y')
    except ValueError:
        pass
    try:
        return datetime.strptime(s[:7], '%Y-%m').strftime('%m/%Y')
    except ValueError:
        pass
    return s


def parse_month_year(value):
    """Returns (month_int, year_int) from a stored expiry value, or
    (None, None) if it can't be parsed — used to pre-select the
    dropdowns on the Edit page."""
    if not value:
        return None, None
    s = str(value).strip()
    for fmt, length in [('%Y-%m-%d', 10), ('%Y-%m', 7)]:
        try:
            d = datetime.strptime(s[:length], fmt)
            return d.month, d.year
        except ValueError:
            continue
    return None, None


@app.route("/chart_data")
def chart_data():
    medicines = get_all_medicines()
    labels = [m["name"] for m in medicines]
    stock = [m["stock"] for m in medicines]
    return jsonify({"labels": labels, "stock": stock})


@app.route("/api/medicines")
def api_medicines():
    if 'user' not in session:
        return jsonify([])
    medicines = get_all_medicines()
    result = []
    for m in medicines:
        d = dict(m)
        d['expiry'] = format_expiry(d.get('expiry'))
        result.append(d)
    return jsonify(result)


@app.route("/api/parties")
def api_parties():
    if 'user' not in session:
        return jsonify([])
    parties = get_all_parties()
    return jsonify([dict(p) for p in parties])


@app.route('/')
def home():
    return redirect('/login')


@app.route('/billing')
def billing():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')


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

    party         = request.form.get('party', '')
    party_address = request.form.get('party_address', '')
    party_gstin   = request.form.get('party_gstin', '')
    party_phone   = request.form.get('party_phone', '')
    party_state   = request.form.get('party_state', '')
    party_d20b    = request.form.get('party_d20b', '')
    party_d21b    = request.form.get('party_d21b', '')
    mode          = request.form.get('mode', 'Cash')

    items = []
    total_qty = 0
    total_gross = 0
    total_disc = 0
    total_taxable = 0
    total_cgst = 0
    total_sgst = 0

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

        total_qty += qty
        total_gross += gross
        total_disc += disc_amt
        total_taxable += taxable
        total_cgst += cgst_amt
        total_sgst += sgst_amt

        items.append({
            "name": names[i],
            "mfr": mfrs[i] if i < len(mfrs) else "",
            "hsn": hsns[i] if i < len(hsns) else "",
            "pack": packs[i] if i < len(packs) else "",
            "batch": batches[i],
            "expiry": format_expiry(expiry[i]) if i < len(expiry) else "",
            "mrp": round(mrp, 2),
            "qty": qty,
            "free": free,
            "rate": rate,
            "gross": round(gross, 2),
            "disc_amt": round(disc_amt, 2),
            "taxable": round(taxable, 2),
            "gst_rate": gst,
            "cgst_rate": cgst_rate,
            "cgst_amt": round(cgst_amt, 2),
            "sgst_rate": sgst_rate,
            "sgst_amt": round(sgst_amt, 2),
            "amount": round(line_total, 2),
        })

        reduce_stock(names[i], batches[i], qty + free)

    tax_summary = {}
    for it in items:
        r = it["gst_rate"]
        if r not in tax_summary:
            tax_summary[r] = {"rate": r, "taxable": 0, "cgst": 0, "sgst": 0}
        tax_summary[r]["taxable"] += it["taxable"]
        tax_summary[r]["cgst"] += it["cgst_amt"]
        tax_summary[r]["sgst"] += it["sgst_amt"]

    net_raw = total_taxable + total_cgst + total_sgst
    rounded_net = round(net_raw)
    rounding_adj = round(rounded_net - net_raw, 2)

    bill_no = create_bill()
    bill_date = datetime.now().strftime('%d/%b/%Y')

    return render_template(
        'invoice.html',
        items=items,
        party=party,
        party_address=party_address,
        party_gstin=party_gstin,
        party_phone=party_phone,
        party_state=party_state,
        party_d20b=party_d20b,
        party_d21b=party_d21b,
        seller_d20b=SELLER_D20B,
        seller_d21b=SELLER_D21B,
        mode=mode,
        bill_no=bill_no,
        bill_date=bill_date,
        total_items=len(items),
        total_units=total_qty,
        total_gross=round(total_gross, 2),
        total_disc=round(total_disc, 2),
        total_taxable=round(total_taxable, 2),
        total_cgst=round(total_cgst, 2),
        total_sgst=round(total_sgst, 2),
        adj=0.00,
        rounding=rounding_adj,
        total=rounded_net,
        tax_summary=list(tax_summary.values()),
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['user'] = username
            return redirect('/billing')

        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


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


@app.route('/add_stock', methods=["GET", "POST"])
def add_stock():
    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":
        def f(key):
            v = request.form.get(key)
            return float(v) if v else 0

        month = request.form.get("expiry_month", "")
        year = request.form.get("expiry_year", "")
        expiry = f"{year}-{month}" if month and year else ""

        add_medicine(
            request.form.get("name"),
            request.form.get("mfr"),
            request.form.get("hsn"),
            request.form.get("pack"),
            request.form.get("batch"),
            expiry,
            f("purchase_price"),
            f("rate"),
            f("mrp"),
            f("gst"),
            int(f("stock")),
        )

    medicines = get_all_medicines()
    current_year = datetime.now().year
    return render_template('add_stock.html', medicines=medicines, current_year=current_year)


@app.route("/edit/<name>/<batch>", methods=["GET", "POST"])
def edit(name, batch):
    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":
        def f(key):
            v = request.form.get(key)
            return float(v) if v else 0

        month = request.form.get("expiry_month", "")
        year = request.form.get("expiry_year", "")
        expiry = f"{year}-{month}" if month and year else ""

        update_medicine(
            name, batch,
            request.form.get("name"),
            request.form.get("mfr"),
            request.form.get("hsn"),
            request.form.get("pack"),
            request.form.get("batch"),
            expiry,
            f("purchase_price"),
            f("rate"),
            f("mrp"),
            f("gst"),
            int(f("stock")),
        )
        return redirect("/add_stock")

    medicine = get_medicine(name, batch)
    med_month, med_year = parse_month_year(medicine['expiry']) if medicine else (None, None)
    current_year = datetime.now().year
    return render_template(
        "edit.html",
        medicine=medicine,
        med_month=med_month,
        med_year=med_year,
        current_year=current_year,
    )


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


@app.route('/alerts')
def alerts():
    if 'user' not in session:
        return redirect('/login')

    low_stock, expiry_soon = get_alerts()
    return render_template('alerts.html', low_stock=low_stock, expiry_soon=expiry_soon)


@app.route('/parties', methods=["GET", "POST"])
def parties():
    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":
        add_party(
            request.form.get("name"),
            request.form.get("address"),
            request.form.get("gstin"),
            request.form.get("phone"),
            request.form.get("state"),
            request.form.get("d20b"),
            request.form.get("d21b"),
        )

    all_parties = get_all_parties()
    return render_template('parties.html', parties=all_parties)


@app.route("/delete_party/<int:party_id>")
def delete_party_route(party_id):
    if 'user' not in session:
        return redirect('/login')
    delete_party(party_id)
    return redirect("/parties")


if __name__ == "__main__":
    app.run(debug=True)