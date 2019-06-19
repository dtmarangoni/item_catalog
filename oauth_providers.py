"""Utility module to provide oauth methods.

It includes:
    connection and get user info from provider;
    disconnection from providers;
    registering of oauth provider user in database.
"""

from flask import g, jsonify
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import json
import requests
import os

from database import db_session, User


def oauth_google(code):
    """Get Google user info following the OAuth process.

    First the Google one time code will be exchanged for an credentials object.
    Then with the valid credentials the user info will be accessed.

    Args:
        code (str): one time Google OAuth code.

    Returns:
        A dictionary with: The user's Google account info: name, email,
        picture and user id; and the oauth token.
            Format: {'user': ..., 'token': ...}

        In case of failure, an error message and status code is returned.
            Format: {'error': ..., 'status': ...}
    """
    # Exchange for a token
    if code:
        try:
            # Upgrade the auth code for a credentials object
            folder_path = os.path.dirname(os.path.abspath(__file__))
            file_path = folder_path + '/static/json/google_client_secrets.json'
            oauth_flow = flow_from_clientsecrets(file_path, scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            return {
                'error': 'Failed to upgrade the authorization code.',
                'status': 401
            }
    else:
        return {
            'error': 'No authorization code received from client.',
            'status': 401
        }

    # Check that the access token is valid.
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
    except requests.exceptions.HTTPError:
        return {
            'error': 'Error with the access token:\n{}'.format(result.json()),
            'status': result.status_code
        }

    # Get user info
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
    except requests.exceptions.HTTPError:
        return {
            'error': 'Error getting user info:\n{}'.format(result.json()),
            'status': result.status_code
        }

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
        A dictionary with: The user's Facebook account info: name, email,
        picture and user id; and the oauth token.
            Format: {'user': ..., 'token': ...}

        In case of failure, an error message and status code is returned.
            Format: {'error': ..., 'status': ...}
    """
    folder_path = os.path.dirname(os.path.abspath(__file__))
    file_path = folder_path + '/static/json/facebook_client_secrets.json'
    client_secrets = json.loads(open(file_path, 'r').read())
    app_id = client_secrets['web']['app_id']
    app_secret = client_secrets['web']['app_secret']

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
        return {
            'error': result.get('error'),
            'status': 401
        }

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
        A dictionary with: success or error message and the status code.
            Format: {'logout': ..., 'status': ...} or
            Format: {'error': ..., 'status': ...}
    """
    if not g.user.provider:
        return jsonify(error='Current user not connected.'), 401

    result = {}
    if g.user.provider == 'google':
        url = 'https://accounts.google.com/o/oauth2/revoke'
        params = {'token': g.user.oauth_token, 'alt': 'json'}
        result = requests.get(url, params=params).json()
    elif g.user.provider == 'facebook':
        facebook_id = g.user.oauth_user_id
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s'\
              % (facebook_id, g.user.oauth_token)
        result = requests.delete(url).json()

    if result.get('error') is None:
        return {
            'logout': 'Successfully disconnected',
            'status': 200
        }
    else:
        return {
            'error': result.get('error'),
            'status': 500
        }


def register_oauth_user(user):
    """Check if the user is registered in database and return it.

    If its a new user, he/she will be registered and also returned.

    Args:
        user (database.User): the user object database model.

    Returns:
        A registered or selected user from database.
    """
    old_user = db_session.query(User).filter_by(email=user.email).first()
    if not old_user:
        user.hash_password("")
        db_session.add(user)
        db_session.commit()
        return user
    else:
        # Updating DB fields in case the values has changed since user
        # registration
        old_user.username = user.username
        old_user.email = user.email
        old_user.picture = user.picture
        old_user.provider = user.provider
        old_user.oauth_user_id = user.oauth_user_id
        old_user.oauth_token = user.oauth_token
        db_session.add(old_user)
        db_session.commit()
        return old_user
