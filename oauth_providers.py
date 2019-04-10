"""Utility module to provide oauth methods.

It includes:
    connection and get user info from provider;
    disconnection from providers;
    registering of oauth provider user in database.
"""

from flask import make_response, g, session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
import requests

from database import db_session, User


def oauth_google(code):
    """Get Google user info following the OAuth process.

    First the Google one time code will be exchanged for an credentials object.
    Then with the valid credentials the user info will be accessed.

    Args:
        code (str): one time Google OAuth code.

    Returns:
        A dictionary with: The user's Google account info: name, email and
            picture; and the oauth token.
            Format: {'user': ..., 'token': ...}
    """
    # Exchange for a token
    if code:
        try:
            # Upgrade the auth code for a credentials object
            oauth_flow = flow_from_clientsecrets(
                './static/json/google_client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the '
                                                'authorization code'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
    else:
        response = make_response(json.dumps('No authorization code '
                                            'received from client'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
    except requests.exceptions.HTTPError:
        response = make_response(json.dumps('Error with the access '
                                            'token:\n' + result.json()),
                                 result.status_code)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Get user info
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
    except requests.exceptions.HTTPError:
        response = make_response(json.dumps('Error getting user info:\n'
                                            + result.json()),
                                 result.status_code)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Return the user data and auth token compiled together in a dict
    data = {'user': result.json(), 'token': credentials.access_token}
    return data


def oauth_facebook(access_token):
    """Get Facebook user info following the OAuth process.

    First the Facebook one time token will be exchanged for an access token.
    Then with the valid token the user info will be accessed.

    Args:
        access_token (str): one time Facebook OAuth token.

    Returns:
        A dictionary with: The user's Facebook account info: name, email and
            picture; and the oauth token.
            Format: {'user': ..., 'token': ...}
    """
    client_secret_file = json.loads(
        open('./static/json/facebook_client_secrets.json', 'r').read())
    app_id = client_secret_file['web']['app_id']
    app_secret = client_secret_file['web']['app_secret']

    # Exchange for a token
    url = 'https://graph.facebook.com/oauth/access_token'
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': access_token}
    result = requests.get(url, params=params).json()

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Use token to get user info from API
    token = result.get('access_token')
    url = 'https://graph.facebook.com/v3.2/me'
    params = {'access_token': token, 'fields': 'name,id,email'}
    user_data = requests.get(url, params=params).json()

    # Get user picture and add to the current data dictionary
    url = 'https://graph.facebook.com/v3.2/me/picture'
    params = {'access_token': token, 'redirect': '0', 'height': '200',
              'width': '200'}
    picture = requests.get(url, params=params).json()
    user_data['picture'] = picture["data"]["url"]

    # Return the user data and auth token compiled together in a dict
    data = {'user': user_data, 'token': token}
    return data


def oauth_disconnect():
    """Revoke the oauth and user's token and reset their login session.

    Returns:
        bool: True for success, False otherwise.
        str: Information about the success or the error.
    """
    if not session['oauth_user_id']:
        response = 'Current user not connected.'
        return False, response

    result = {}
    if session['provider'] == 'google':
        url = 'https://accounts.google.com/o/oauth2/revoke'
        params = {'token': session['oauth_token'], 'alt': 'json'}
        result = requests.get(url, params=params).json()
    elif session['provider'] == 'facebook':
        facebook_id = session['oauth_user_id']
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s'\
              % (facebook_id, session['oauth_token'])
        result = requests.delete(url).json()

    if result.get('error') is None:
        response = 'Successfully disconnected.'
        return True, response
    else:
        response = 'Failed to revoke token for the given user.'
        return False, response


def register_oauth_user(user):
    """Check if the user is registered in database and return it.

    If its a new user, he/she will be registered and also returned.

    Args:
        user (database.User): the user database model.

    Returns:
        A registered or selected user from database.
    """
    old_user = db_session.query(User).filter_by(email=user.email).first()
    if not old_user:
        new_user = User(username=user.username, email=user.email,
                        picture=user.picture)
        new_user.hash_password("")
        db_session.add(new_user)
        db_session.commit()
        return new_user
    else:
        return old_user
