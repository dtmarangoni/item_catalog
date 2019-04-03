from flask import Flask, render_template, jsonify
import random
import string

from database import db_session, User, Category, Item


# Create app
app = Flask(__name__)
app.config['DEBUG'] = True

# Using secrets module only available on Python 3.6 or above
# state = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
#                for _ in range(32))
app.config['SECRET_KEY'] = ''.join(random.SystemRandom().choice(
    string.ascii_uppercase + string.digits) for _ in range(32))


# Automatically remove database sessions at the end of the request or when
# the application shuts down
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions.
     This is done at the end of the request or when the application shuts
     down.
     """
    db_session.remove()


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


@app.route('/catalog/api/v1/json')
def catalog_json():
    """API end point for sending all catalog in a JSON format."""
    categories = db_session.query(Category).all()
    items = db_session.query(Item).all()
    catalog = []
    for c in categories:
        cat = c.serialize
        cat['Item'] = [i.serialize for i in items if i.category_id == c.id]
        catalog.append(cat)

    return jsonify(Category=catalog)


if __name__ == '__main__':
    """Running from command line starts the Flask application."""
    app.run(host='0.0.0.0', port=5000)
