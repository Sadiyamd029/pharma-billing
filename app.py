from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


# IMPORTANT: allow BOTH GET and POST
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if request.method == 'POST':
        names = request.form.getlist('name')
        batches = request.form.getlist('batch')
        qtys = request.form.getlist('qty')
        rates = request.form.getlist('rate')

        items = []
        total = 0

        for i in range(len(names)):
            try:
                name = names[i]
                batch = batches[i]
                qty = float(qtys[i])
                rate = float(rates[i])
                amount = qty * rate
                total += amount

                items.append({
                    'name': name,
                    'batch': batch,
                    'qty': qty,
                    'rate': rate,
                    'amount': amount
                })
            except:
                continue

        return render_template('invoice.html', items=items, total=total)

    # If someone opens /billing directly
    return "Use form to generate bill"

if __name__ == '__main__':
    app.run(debug=True)