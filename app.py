from flask import Flask, render_template, request, redirect, session, send_file
from functools import wraps
from db import (
    init_db,
    reduce_stock,
    add_medicine,
    get_all_medicines,
    get_alerts,
    create_user,
    check_user,
    update_medicine,
    delete_medicine
)
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


# 🏠 HOME
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# 🔐 LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        role = check_user(username, password)

        if role:
            session["user"] = username
            session["role"] = role
            return redirect("/dashboard")
        else:
            return "Invalid Login"

    return render_template("login.html")


# 🔓 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# 🧾 BILLING
@app.route('/billing', methods=['GET', 'POST'])
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

        # ✅ STORE IN SESSION (IMPORTANT)
        session["invoice_items"] = items
        session["invoice_total"] = round(total, 2)

    return render_template(
        "index.html",
        items=session.get("invoice_items", []),
        total=session.get("invoice_total", 0)
    )


# 📄 DOWNLOAD PDF (FIXED)
@app.route("/download_pdf", methods=["GET"])
@login_required
def download_pdf():
    items = session.get("invoice_items", [])
    total = session.get("invoice_total", 0)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    y = 750

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, y, "Pharma Invoice")

    y -= 40

    c.setFont("Helvetica", 10)

    headers = ["Name", "Batch", "Qty", "Rate", "GST", "Total"]
    x = [50, 120, 200, 260, 320, 380]

    for i, h in enumerate(headers):
        c.drawString(x[i], y, h)

    y -= 20

    for item in items:
        c.drawString(50, y, str(item["name"]))
        c.drawString(120, y, str(item["batch"]))
        c.drawString(200, y, str(item["qty"]))
        c.drawString(260, y, str(item["rate"]))
        c.drawString(320, y, str(item["gst"]))
        c.drawString(380, y, str(item["amount"]))
        y -= 20

    y -= 20
    c.drawString(50, y, f"Total: {total}")

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="invoice.pdf",
        mimetype="application/pdf"
    )


# 🧠 INIT
init_db()
create_user("admin", "irfan1016", "admin")


# 🚀 RUN
if __name__ == "__main__":
    app.run(debug=True)