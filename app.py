from flask import Flask, render_template, request, redirect, session
from functools import wraps
from db import init_db, reduce_stock, add_medicine, get_all_medicines, get_alerts
from db import create_user, check_user
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import json


app = Flask(__name__)
app.secret_key = "supersecretkey"


# 🔒 LOGIN REQUIRED
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


# 🔐 LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if check_user(username, password):
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid Login"

    return render_template("login.html")


# 🔓 LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# 🧾 BILLING
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    total = 0
    items = []

    if request.method == "POST":
        names = request.form.getlist("name")
        batchs = request.form.getlist("batch")
        qtys = request.form.getlist("qty")
        rates = request.form.getlist("rate")
        gsts = request.form.getlist("gst")

        for i in range(len(names)):
            if not names[i]:
                continue

            try:
                qty = float(qtys[i])
                rate = float(rates[i])
                gst = float(gsts[i])
            except:
                continue

            amount = qty * rate
            gst_amount = amount * gst / 100
            total_item = amount + gst_amount

            total += total_item

            reduce_stock(names[i], batchs[i], int(qty))

            items.append({
                "name": names[i],
                "batch": batchs[i],
                "qty": qty,
                "rate": rate,
                "gst": gst,
                "amount": round(total_item, 2)
            })

    return render_template("index.html", items=items, total=round(total, 2))


# ➕ ADD STOCK
@app.route("/add_stock", methods=["GET", "POST"])
@login_required
def add_stock():
    if request.method == "POST":
        add_medicine(
            request.form.get("name"),
            request.form.get("batch"),
            request.form.get("expiry"),
            int(request.form.get("stock"))
        )

    medicines = get_all_medicines()
    return render_template("add_stock.html", medicines=medicines)


# ⚠️ ALERTS
@app.route("/alerts")
@login_required
def alerts():
    low_stock, expiry_soon = get_alerts()
    return render_template("alerts.html",
                           low_stock=low_stock,
                           expiry_soon=expiry_soon)


# 📊 DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    medicines = get_all_medicines()

    total_medicines = len(medicines)
    total_stock = sum([m[3] for m in medicines]) if medicines else 0

    low_stock, expiry_soon = get_alerts()

    return render_template(
        "dashboard.html",
        total_medicines=total_medicines,
        total_stock=total_stock,
        low_stock=len(low_stock),
        expiry_soon=len(expiry_soon)
    )
    
    # 🧾 DOWNLOAD PDF
@app.route("/download_pdf")
@login_required
def download_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    y = 750

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, y, "Pharma Invoice")

    y -= 40

    # Table headers
    c.setFont("Helvetica", 10)
    headers = ["Name", "Batch", "Qty", "Rate", "GST", "Total"]
    x = [50, 120, 200, 260, 320, 380]

    for i, h in enumerate(headers):
        c.drawString(x[i], y, h)

    y -= 20

    # Get items
    items = request.args.get("items")

    if items:
        items = json.loads(items)

        for item in items:
            c.drawString(50, y, str(item["name"]))
            c.drawString(120, y, str(item["batch"]))
            c.drawString(200, y, str(item["qty"]))
            c.drawString(260, y, str(item["rate"]))
            c.drawString(320, y, str(item["gst"]))
            c.drawString(380, y, str(item["amount"]))
            y -= 20

    c.save()
    buffer.seek(0)

    return send_file(buffer,
                     as_attachment=True,
                     download_name="invoice.pdf",
                     mimetype="application/pdf")


# 🧠 INIT DB
init_db()

# 👤 DEFAULT USER (RUN ONCE ONLY)
create_user("admin", "admin123")


# 🚀 RUN
if __name__ == "__main__":
    app.run(debug=True)