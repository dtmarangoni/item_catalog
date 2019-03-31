from flask import Flask, render_template


app = Flask(__name__)


# Views

# Index page that shows the ten latest added items
@app.route('/')
@app.route('/catalog')
def catalog():
    return render_template('catalog.html')


# Page for showing items from a specific category
@app.route('/catalog/<string:category>')
def category(category):
    return render_template('category.html', category=category)


# Page for showing item information
@app.route('/catalog/<string:category>/<string:item>')
def item(category, item):
    return render_template('item.html')


# Page for add an item
@app.route('/catalog/<string:category>/add')
def add_item(category):
    return render_template('add_item.html', category=category)


# Page for editing an item
@app.route('/catalog/<string:category>/<string:item>/edit')
def edit_item(category, item):
    return render_template('edit_item.html', category=category)


# Page for deleting an item
@app.route('/catalog/<string:category>/<string:item>/delete')
def delete_item(category, item):
    return render_template('delete_item.html')


# Login page
@app.route('/catalog/login')
def login():
    return render_template('login.html')


# New user page
@app.route('/catalog/new_user')
def new_user():
    return render_template('new_user.html')


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
