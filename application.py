from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask import flash
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

# Load the pre-defined DB categories.
categories = db_session.query(Category).all()


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

@app.route('/')
@app.route('/catalog')
def catalog():
    """Index page that shows the latest added items in the catalog."""
    items = db_session.query(Item).order_by(Item.id.desc()).limit(10)
    return render_template('catalog.html', categories=categories, items=items)


@app.route('/catalog/<string:category>')
def category(category):
    """Shows all items added to a specific category."""
    items = db_session.query(Item).join(Category).filter(
        Category.name == category).all()
    return render_template('category.html', categories=categories,
                           category=category, items=items)


@app.route('/catalog/<string:category>/<string:item>')
def item(category, item):
    """Page for showing an item information."""
    item = db_session.query(Item).filter_by(name=item).one()
    return render_template('item.html', categories=categories,
                           category=category, item=item)


@app.route('/catalog/<string:category>/add', methods=['GET', 'POST'])
def add_item(category):
    """Route for item adding page or to process form submission.
    The item data from form will be added in the database.
    """
    if request.method == 'GET':
        return render_template('add_item.html', categories=categories,
                               category=category)
    elif request.method == 'POST':
        print('\n\n')
        print(request.form['category'])
        print('\n\n')
        cat = db_session.query(Category).filter_by(
            name=request.form['category']).one()
        item = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=cat.id
        )
        db_session.add(item)
        db_session.commit()
        flash('New Menu Item Created.')
        return redirect(url_for('catalog'))


# Page for editing an item
@app.route('/catalog/<string:category>/<string:item>/edit')
def edit_item(category, item):
    return render_template('edit_item.html', categories=categories,
                           category=category, item=item)


# Page for deleting an item
@app.route('/catalog/<string:category>/<string:item>/delete')
def delete_item(category, item):
    return render_template('delete_item.html', categories=categories)


# Login page
@app.route('/catalog/login')
def login():
    return render_template('login.html', categories=categories)


# New user page
@app.route('/catalog/new_user')
def new_user():
    return render_template('new_user.html', categories=categories)


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
