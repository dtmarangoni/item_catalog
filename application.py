from flask import Flask, render_template, jsonify, request
from flask import g, session, flash, make_response, redirect, url_for
from flask_httpauth import HTTPBasicAuth
import random
import string
import json

from database import db_session, User, Category, Item
from oauth_providers import oauth_google, oauth_facebook, register_oauth_user
from oauth_providers import oauth_disconnect


# Create app
app = Flask(__name__)
app.config['DEBUG'] = True

# Using secrets module only available on Python 3.6 or above
# state = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
#                for _ in range(32))
app.config['SECRET_KEY'] = ''.join(random.SystemRandom().choice(
    string.ascii_uppercase + string.digits) for _ in range(32))

# Create the basic Flask HTTP Auth
auth = HTTPBasicAuth()

# Load the pre-defined DB categories.
categories = db_session.query(Category).all()


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions.
    This is done at the end of the request or when the application shuts down.
    """
    db_session.remove()


@auth.error_handler
def auth_error():
    """Called by Flask when an authentication error occurs."""
    response = make_response(json.dumps('Authentication error'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response


# Views

@app.route('/')
@app.route('/catalog')
def catalog():
    """Index page that shows the latest added items in the catalog."""
    items = db_session.query(Item).order_by(Item.id.desc()).limit(9)
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
    # Anonymous users cant add items. They must login first
    if not session.get('user_id'):
        return redirect(url_for('site_login'))

    if request.method == 'GET':
        return render_template('add_item.html', categories=categories,
                               category=category)
    elif request.method == 'POST':
        cat = db_session.query(Category).filter_by(
            name=request.form['category']).one()
        item = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=cat.id,
            user_id=session['user_id']
        )
        db_session.add(item)
        db_session.commit()
        return redirect(url_for('catalog'))


@app.route('/catalog/<string:category>/<string:item>/edit',
           methods=['GET', 'POST'])
def edit_item(category, item):
    """Route for item editing page or to process form submission.
    The item data from form will be updated in the database.
    """
    # Anonymous users cant edit items. They must login first
    if not session.get('user_id'):
        return redirect(url_for('site_login'))

    i = db_session.query(Item).join(Category).filter(
        Item.name == item, Category.name == category).one()

    # Unauthorized users cant edit items from other users.
    # The HTML pages are protected but this is implemented to avoid manually
    # url user access to this route and item editing.
    if session.get('user_id') != i.user_id:
        response = make_response(
            json.dumps("Unauthorized. You can't edit others user's item."),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if request.method == 'GET':
        return render_template('edit_item.html', categories=categories,
                               category=category, item=i)
    elif request.method == 'POST':
        i.name = request.form['name']
        i.description = request.form['description']

        # In case of category change, we need the new ID
        cat = db_session.query(Category).filter_by(
            name=request.form['category']).one()
        i.category_id = cat.id
        db_session.add(i)
        db_session.commit()
        return redirect(url_for('catalog'))


@app.route('/catalog/<string:category>/<string:item>/delete',
           methods=['GET', 'POST'])
def delete_item(category, item):
    """Route for item deleting page or to process form submission.
    After confirmation, the item from form will be deleted from database.
    """
    # Anonymous users cant delete items. They must login first
    if not session.get('user_id'):
        return redirect(url_for('site_login'))

    i = db_session.query(Item).join(Category).filter(
        Item.name == item, Category.name == category).one()

    # Unauthorized users cant delete items from other users.
    # The HTML pages are protected but this is implemented to avoid manually
    # url user access to this route and item deleting.
    if session.get('user_id') != i.user_id:
        response = make_response(
            json.dumps("Unauthorized. You can't delete others user's item."),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if request.method == 'GET':
        return render_template('delete_item.html', categories=categories,
                               category=category, item=i)
    elif request.method == 'POST':
        db_session.delete(i)
        db_session.commit()
        return redirect(url_for('catalog'))


@app.route('/catalog/api/v1/catalog.json')
@auth.login_required
def catalog_json():
    """API end point for sending all catalog in JSON format."""
    categories = db_session.query(Category).all()
    items = db_session.query(Item).all()
    catalog = []
    for c in categories:
        cat = c.serialize
        cat['Item'] = [i.serialize for i in items if i.category_id == c.id]
        catalog.append(cat)

    return jsonify(Catalog=catalog)


@app.route('/catalog/api/v1/<string:category>.json')
@auth.login_required
def category_json(category):
    """API end point for getting the category and items inside of it.
    The return is a response in JSON format."""
    c = db_session.query(Category).filter_by(name=category).first()
    items = db_session.query(Item).filter_by(category_id=c.id)
    cat = c.serialize
    cat['Item'] = [item.serialize for item in items]
    return jsonify(Category=cat)


@app.route('/catalog/api/v1/<string:category>/<string:item>.json')
@auth.login_required
def item_json(category, item):
    """API end point for getting an item information in JSON format."""
    i = db_session.query(Item).join(Category).filter(
        Item.name == item, Category.name == category).first()
    return jsonify(Item=i.serialize)


@app.route('/catalog/site_login', methods=['GET', 'POST'])
def site_login():
    """Route for login page or to process site login form submission."""
    if request.method == 'GET':
        return render_template('login.html', categories=categories)
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_password(username, password):
            return redirect(url_for('catalog'))
        else:
            flash('Invalid username and/or login.')
            return redirect(url_for('login'))


@app.route('/catalog/oauth_login/<string:provider>', methods=['POST'])
def oauth_login(provider):
    """Route for oauth providers login."""
    if provider == 'google':
        # Parse de auth code
        g_code = request.data
        # Get user info and oauth token
        data = oauth_google(g_code)
    elif provider == 'facebook':
        # Parse de auth code
        f_token = request.data
        # Get user info and oauth token
        data = oauth_facebook(f_token)
    else:
        response = make_response(json.dumps('Unrecognized provider'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if user is already registered in DB. If not, add it.
    user_data = data['user']
    oauth_token = data['token']
    user = User(username=user_data['name'], email=user_data['email'],
                picture=user_data['picture'])
    user = register_oauth_user(user)
    # Add user to g and provider info to session
    g.user = user
    session['user_id'] = user.id
    session['provider'] = provider
    session['oauth_user_id'] = user_data['id']
    session['oauth_token'] = oauth_token
    session['user_token'] = user.gen_auth_token()

    return redirect(url_for('catalog'))


@app.route('/catalog/login/disconnect')
def disconnect():
    """Revoke a current user's token and reset his login session."""
    if session.get('provider'):
        status, response = oauth_disconnect()
        if status:
            g.user = None
            session.clear()
        else:
            print('\n' + response + '\n')
    else:
        g.user = None
        session.clear()

    return redirect(url_for('catalog'))


@app.route('/catalog/new_user', methods=['GET', 'POST'])
def new_user():
    """Route for new user login page or to process form submission.
    After the user is created the site is redirected to the main page.
    """
    if request.method == 'GET':
        return render_template('new_user.html', categories=categories)
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Verify if the username is already registered in DB
        u = db_session.query(User).filter_by(username=username).first()
        if u:
            flash('Username already in use. Please choose another one.')
            return redirect(url_for('new_user'))

        # Verify if the email is already registered in DB
        u = db_session.query(User).filter_by(email=email).first()
        if u:
            flash('E-mail already registered in the site.')
            return redirect(url_for('new_user'))

        user = User(username=username, email=email)
        user.hash_password(password)
        db_session.add(user)
        db_session.commit()
        g.user = user
        session['user_id'] = user.id
        session['user_token'] = user.gen_auth_token()
        return redirect(url_for('catalog'))


# Use @auth.login_required to require a login in order to access a
# resource. It will call @auth.verify_password
@app.route('/catalog/token')
@auth.login_required
def get_app_token():
    """API end point for getting an user access token.

    Returns:
        The access token returned as a Flask response in JSON format.
    """
    token = g.user.gen_auth_token()
    return jsonify({'token': token.decode('ascii')})


# Utility methods.

@auth.verify_password
def verify_password(username_or_token, password):
    """Called by Flask when the login is required.

    Args:
        username_or_token (str): the login username or auth token.
        password (str): the login password. Blank when the login method is
        by authentication token.

    Returns:
        bool: True for success, False otherwise.
    """
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = db_session.query(User).filter_by(id=user_id).one()
        # Valid token, add it to the session
        session['user_token'] = username_or_token
    else:
        user = db_session.query(User).filter_by(
            username=username_or_token).first()
        if (not user) or (not user.verify_password(password)):
            return False
        else:
            # No token yet, so generate one.
            session['user_token'] = user.gen_auth_token()
    g.user = user
    session['user_id'] = user.id
    return True


@app.route('/catalog/api/v1/users')
def users_json():
    """API end point for sending all registered users in a JSON format."""
    users = db_session.query(User).all()
    return jsonify(Users=[user.serialize for user in users])


if __name__ == '__main__':
    """Running from command line starts the Flask application."""
    app.run(host='0.0.0.0', port=5000)
