#!/usr/bin/env python3
#
"""The Flask application with routes treatment.

The app will interact with Database through SQLAlchemy. And with oauth
providers through project defined functions in oauth_providers module.

The routes' protection are performed using JWT.
Revoked JWT tokens are blacklisted and controlled through Redis.
Redis will also be used to control the throughput of user requests to the site.
"""

from flask import (
    Flask, render_template, jsonify, request, g, flash, redirect, url_for
)
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, create_access_token,
    jwt_refresh_token_required, create_refresh_token, get_jwt_identity,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies, get_csrf_token
)
import random
import string
import json

from database import db_session, User, Category, Item
from oauth_providers import (
    oauth_google, oauth_facebook, register_oauth_user, oauth_disconnect
)


# Create app
app = Flask(__name__)
app.config['DEBUG'] = False

# Configure application to store JWTs in cookies
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

# Only allow JWT cookies to be sent over https. In production, change this
# to True
app.config['JWT_COOKIE_SECURE'] = False

# Set the cookie paths, so that you are only sending your access token
# cookie to the access endpoints, and only sending your refresh token
# to the refresh endpoint. Technically this is optional, but it is in
# your best interest to not send additional cookies in the request if
# they aren't needed.
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/'

# Enable csrf double submit protection. See this for a thorough
# explanation: http://www.redotheweb.com/2015/11/09/api-security.html
app.config['JWT_COOKIE_CSRF_PROTECT'] = True

# Using secrets module only available on Python 3.6 or above
# state = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
#                for _ in range(32))
app.config['SECRET_KEY'] = ''.join(random.SystemRandom().choice(
    string.ascii_uppercase + string.digits) for _ in range(32))
app.config['JWT_SECRET_KEY'] = ''.join(random.SystemRandom().choice(
    string.ascii_uppercase + string.digits) for _ in range(32))

# Create the JWTManager linked to Flask app
jwt = JWTManager(app)

# Load the pre-defined DB categories.
categories = db_session.query(Category).all()

# Load the Oauth client IDs from JSON file
with app.open_resource('./static/json/google_client_secrets.json') as f:
    g_client_id = json.load(f)['web']['client_id']

with app.open_resource('./static/json/facebook_client_secrets.json') as f:
    f_client_id = json.load(f)['web']['app_id']


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Automatically remove database sessions.

    This is done at the end of the request or when the application shuts down.
    """
    db_session.remove()


# Views

@app.route('/')
@app.route('/catalog')
@jwt_optional
def catalog():
    """Index page that shows the latest added items in the catalog."""
    items = db_session.query(Item).order_by(Item.id.desc()).limit(9)
    return render_template('catalog.html', categories=categories, items=items)


@app.route('/catalog/<string:category>')
@jwt_optional
def category(category):
    """Show all items added to a specific category."""
    items = db_session.query(Item).join(Category).filter(
        Category.name == category).all()
    return render_template('category.html', categories=categories,
                           category=category, items=items)


@app.route('/catalog/<string:category>/<string:item>')
@jwt_optional
def item(category, item):
    """Page for showing an item information."""
    item = db_session.query(Item).filter_by(name=item).first()
    return render_template('item.html', categories=categories,
                           category=category, item=item)


@app.route('/catalog/<string:category>/add', methods=['GET', 'POST'])
@jwt_required
def add_item(category):
    """Route for item adding page or to process form submission.

    The item data from form will be added in the database.
    """
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
            user_id=g.user.id
        )
        db_session.add(item)
        db_session.commit()
        return redirect(url_for('catalog'), code=303)


@app.route('/catalog/<string:category>/<string:item>/edit',
           methods=['GET', 'PUT'])
@jwt_required
def edit_item(category, item):
    """Route for item editing page or to process form submission.

    The item data from form will be updated in the database.
    """
    i = db_session.query(Item).join(Category).filter(
        Item.name == item, Category.name == category).first()

    # Unauthorized users can't edit items from other users.
    # The HTML pages are protected but this is implemented to avoid manually
    # user access to this url route thus performing unauthorized item edition.
    if g.user.id != i.user_id:
        return jsonify(
            error="Unauthorized. You can't edit others user's item."), 401

    if request.method == 'GET':
        return render_template('edit_item.html', categories=categories,
                               category=category, item=i)
    elif request.method == 'PUT':
        i.name = request.form['name']
        i.description = request.form['description']

        # In case of category change, we need the new ID
        cat = db_session.query(Category).filter_by(
            name=request.form['category']).one()
        i.category_id = cat.id
        db_session.add(i)
        db_session.commit()
        return redirect(url_for('catalog'), code=303)


@app.route('/catalog/<string:category>/<string:item>/delete',
           methods=['GET', 'DELETE'])
@jwt_required
def delete_item(category, item):
    """Route for item deleting page or to process form submission.

    After confirmation, the item from form will be deleted from database.
    """
    i = db_session.query(Item).join(Category).filter(
        Item.name == item, Category.name == category).first()

    # Unauthorized users can't delete items from other users.
    # The HTML pages are protected but this is implemented to avoid manually
    # user access to this url route thus performing unauthorized item deletion.
    if g.user.id != i.user_id:
        return jsonify(
            error="Unauthorized. You can't delete others user's item."), 401

    if request.method == 'GET':
        return render_template('delete_item.html', categories=categories,
                               category=category, item=i)
    elif request.method == 'DELETE':
        db_session.delete(i)
        db_session.commit()
        return redirect(url_for('catalog'), code=303)


@app.route('/catalog/api/v1/catalog.json')
@jwt_required
def catalog_json():
    """API end point for sending all catalog in JSON format.

    Returns:
        A response in JSON format.
    """
    categories = db_session.query(Category).all()
    items = db_session.query(Item).all()
    catalog = []
    for c in categories:
        cat = c.serialize
        cat['Item'] = [i.serialize for i in items if i.category_id == c.id]
        catalog.append(cat)

    return jsonify(Catalog=catalog)


@app.route('/catalog/api/v1/<string:category>.json')
@jwt_required
def category_json(category):
    """API end point for getting the category and items inside of it.

    Returns:
        A response in JSON format.
    """
    c = db_session.query(Category).filter_by(name=category).first()
    items = db_session.query(Item).filter_by(category_id=c.id)
    cat = c.serialize
    cat['Item'] = [item.serialize for item in items]
    return jsonify(Category=cat)


@app.route('/catalog/api/v1/<string:category>/<string:item>.json')
@jwt_required
def item_json(category, item):
    """API end point for getting an item information in JSON format.

    Returns:
        A response in JSON format.
    """
    i = db_session.query(Item).join(Category).filter(
        Item.name == item, Category.name == category).first()
    return jsonify(Item=i.serialize)


@app.route('/catalog/site_login', methods=['GET', 'POST'])
def site_login():
    """Route for login page or to process site login form submission.

    After the user is logged the site is redirected to the main page and
    the jwt access and refresh tokens are sent back trough cookies.
    """
    if request.method == 'GET':
        return render_template('login.html',
                               categories=categories,
                               g_client_id=g_client_id,
                               f_client_id=f_client_id)
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db_session.query(User).filter_by(username=username).first()
        if (not user) or (not user.verify_password(password)):
            flash('Invalid username and/or password.')
            return redirect(url_for('site_login'), code=303)
        else:
            g.user = user
            response = redirect(url_for('catalog'), code=303)
            response = set_jwt_token(response)
            return response


@app.route('/catalog/oauth_login/<string:provider>', methods=['POST'])
def oauth_login(provider):
    """Route for oauth providers login."""
    if provider == 'google':
        # Parse de auth code
        g_code = request.data
        # Get user info and oauth token
        resp = oauth_google(g_code)
    elif provider == 'facebook':
        # Parse de auth code
        f_token = request.data
        # Get user info and oauth token
        resp = oauth_facebook(f_token)
    else:
        flash('Unrecognized provider')
        return redirect(url_for('site_login'), code=303)

    if resp.get('error'):
        print('\n{}\n'.format(resp.get('error')))
        return redirect(url_for('site_login'), code=303)

    # Check if user is already registered in DB. If not, add it.
    user_data = resp['user']
    oauth_token = resp['token']
    user = User(username=user_data['name'],
                email=user_data['email'],
                picture=user_data['picture'],
                provider=provider,
                oauth_user_id=user_data['id'],
                oauth_token=oauth_token
                )
    user = register_oauth_user(user)

    g.user = user
    response = redirect(url_for('catalog'), code=303)
    response = set_jwt_token(response)
    return response


@app.route('/catalog/login/disconnect')
@jwt_required
def disconnect():
    """Logout and revoke a current user's tokens.

     The site is redirected to the main page.
     """
    if g.get('user'):
        if g.user.provider:
            response = oauth_disconnect()
            if response.get('error'):
                return jsonify(
                    error=response.get('error')
                ), response.get('status')

        g.user = None

    response = redirect(url_for('catalog'), code=303)
    unset_jwt_cookies(response)
    return response


@app.route('/catalog/new_user', methods=['GET', 'POST'])
def new_user():
    """Route for new user login page or to process form submission.

    After the user is created the site is redirected to the main page and
    the jwt access and refresh tokens are sent back trough cookies.
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
            return redirect(url_for('new_user'), code=303)

        # Verify if the email is already registered in DB
        u = db_session.query(User).filter_by(email=email).first()
        if u:
            flash('E-mail already registered in the site.')
            return redirect(url_for('new_user'), code=303)

        user = User(username=username, email=email)
        user.hash_password(password)
        db_session.add(user)
        db_session.commit()
        g.user = user
        response = redirect(url_for('catalog'), code=303)
        response = set_jwt_token(response)
        return response


# Same thing as login here, except we are only setting a new cookie
# for the access token.
@app.route('/catalog/api/v1/token/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh_app_token():
    """API end point for refreshing an user access token.

    The access token is updated in the cookie.
    """
    # Create the new access token
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)

    # Set the access JWT and CSRF double submit protection cookies
    # in this response
    resp = jsonify(refresh=True)
    set_access_cookies(resp, access_token)
    return resp, 200


# Utility methods.

def set_jwt_token(response):
    """Set the JWT access and refresh tokens in cookies in the response object.

    Args:
        response: A flask response object where the tokens' cookies will be
        set.

    Returns:
        obj: The same response object with cookies set.
    """
    # Create the tokens we will be sending back to the user
    access_token = create_access_token(identity=g.user.id)
    refresh_token = create_refresh_token(identity=g.user.id)

    # Set the JWTs and the CSRF double submit protection cookies in the
    # response
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    return response


# This function is called whenever a protected endpoint is accessed,
# and must return an object based on the tokens identity.
# This is called after the token is verified, so you can use
# get_jwt_claims() in here if desired. Note that this needs to
# return None if the user could not be loaded for any reason,
# such as not being found in the underlying data store
@jwt.user_loader_callback_loader
def get_db_user(identity):
    """This function receives the user identity and load it from DB.

    The user is set in the global flask variable g.

    Args:
        identity (int): the user id.

    Returns:
        The user obj loaded from DB or None if it's not found.
    """
    user = db_session.query(User).filter_by(id=identity).first()
    if user is None:
        return None

    g.user = user
    return user


@jwt.expired_token_loader
@jwt.invalid_token_loader
@jwt.revoked_token_loader
def invalid_token(*args, **kwargs):
    """This function will be run every time an non-valid token is received.

    This will happen when non-valid tokens (invalid, expired or revoked)
    try to access a protected endpoint.
    """
    for arg in args:
        print('\nNon-valid token: {}\n'.format(arg))
    for key, value in kwargs.items():
        print('\n{}: {}\n'.format(key, value))

    response = redirect(url_for('catalog'), code=303)
    unset_jwt_cookies(response)
    return response


if __name__ == '__main__':
    """Running from command line starts the Flask application."""
    app.run(host='0.0.0.0', port=5000)
