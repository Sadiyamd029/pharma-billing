from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if request.method == 'POST':

        party_name = request.form.get('party_name')

        names = request.form.getlist('name[]')
        batch = request.form.getlist('batch[]')
        expiry = request.form.getlist('expiry[]')
        qty = request.form.getlist('qty[]')
        rate = request.form.getlist('rate[]')

        items = []
        total = 0

        for i in range(len(names)):
            if names[i] == '':
                continue

            q = float(qty[i])
            r = float(rate[i])
            t = q * r
            total += t

            items.append({
                'name': names[i],
                'batch': batch[i],
                'expiry': expiry[i],
                'qty': q,
                'rate': r,
                'total': t
            })

        return render_template('invoice.html',
                               items=items,
                               total=total,
                               party_name=party_name)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)