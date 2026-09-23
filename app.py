import os
from functools import wraps

from flask import Flask, render_template, request, redirect, session, jsonify, url_for

import db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

db.init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect(url_for("dashboard") if "user" in session else url_for("login"))


# ---------------- LOGIN / SIGNUP ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = db.check_user(username, password)
        if role:
            session["user"] = username
            session["role"] = role
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("signup.html", error="Username and password are required")
        if db.create_user(username, password):
            return redirect(url_for("login"))
        return render_template("signup.html", error="That username is already taken")
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    total_medicines, total_stock, low_stock, expiry_soon = db.get_dashboard_stats()
    return render_template(
        "dashboard.html",
        total_medicines=total_medicines,
        total_stock=total_stock,
        low_stock=low_stock,
        expiry_soon=expiry_soon,
    )


@app.route("/chart_data")
@login_required
def chart_data():
    labels, stock = db.get_chart_data()
    return jsonify({"labels": labels, "stock": stock})


# ---------------- BILLING ----------------
@app.route("/billing", methods=["GET", "POST"])
@login_required
def billing():
    items = []
    total = 0.0

    if request.method == "POST":
        names = request.form.getlist("name")
        batches = request.form.getlist("batch")
        qtys = request.form.getlist("qty")
        rates = request.form.getlist("rate")
        gsts = request.form.getlist("gst")

        for i in range(len(names)):
            if not names[i]:
                continue
            try:
                qty = float(qtys[i])
                rate = float(rates[i])
                gst = float(gsts[i]) if gsts[i] else 0.0
            except ValueError:
                continue

            subtotal = qty * rate
            amount = subtotal + (subtotal * gst / 100)
            total += amount

            items.append({
                "name": names[i],
                "batch": batches[i],
                "qty": qty,
                "amount":