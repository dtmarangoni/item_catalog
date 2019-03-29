from flask import Flask, render_template


app = Flask(__name__)


# Views

# Index page that shows the ten latest added items
@app.route('/')
@app.route('/catalog')
def catalog():
    return render_template('catalog.html')


# Page for showing item information
@app.route('/catalog/<string:category>/<string:item>')
def item(category, item):
    return render_template('item.html')


# Page for editing an item
@app.route('/catalog/<string:category>/<string:item>/edit')
def edit_item(category, item):
    return render_template('edit_item.html')


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
