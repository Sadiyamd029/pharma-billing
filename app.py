from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/billing')
def billing():
    return render_template('index.html')

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
                "total": item_total
            })
        except:
            continue

    return render_template('invoice.html', items=items, total=total)


# 🔥 ADD THESE ROUTES (your missing pages)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/add_stock')
def add_stock():
    return render_template('add_stock.html')

@app.route('/alerts')
def alerts():
    return render_template('alerts.html')


if __name__ == '__main__':
    app.run(debug=True)