# Item Catalog

An Item Catalog full web application made from scratch from frontend to backend.

As first step, the app will provide a list of pre-defined 
categories, as well an user registration and authentication system.

Registered users will have the ability to post, edit and delete their own items.

Third party user authentication implemented with Google and Facebook.

Technologies envolved: HTML, CSS, Bootstrap, Python, Flask, SQLAlchemy and OAuth authentication.


## Requirements

In order to run this app you will need:
- Vagrant and Oracle VirtualBox. Versions used and tested:
    - [Vagrant](https://www.vagrantup.com/downloads.html). Install the version for your system;
    - [VirtualBox 5.1](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1).
- Clone or download the project files. It includes the source codes, html templates, css stylesheet, some images and Vagrant configuration file. Get from [here](https://github.com/dtmarangoni/item_catalog.git);
- JSON files containing client secrets information. This project implement connections to Facebook and Google.
    - Access the links to create a web application and oauth credentials.
        - [Facebook Developers](https://developers.facebook.com/). Include the `http://localhost:5000` as site URL;
        - [Google Developers Console](https://console.developers.google.com). Include the `http://localhost:5000` as Javascript authorized origins and authorized URIs for redirection;
    - After finished, download the JSON file from Google and place it in `static/json` inside project folder. Rename it to `google_client_secrets.json`.
    - The Facebook JSON file must be manually created. A template example is already inside the folder - `facebook_client_secrets.json`.
- Python 3 installed in Vagrant Linux VM(not tested with Python 2);
- If not already, please install pip3 and Python 3 modules:
  - pip3:
    - `sudo apt-get install python3-pip`;
    - `sudo pip3 install --upgrade pip`.
  - sqlalchemy: `sudo pip3 install sqlalchemy`;
  - passlib: `sudo pip3 install passlib`;
  - itsdangerous: `sudo pip3 install itsdangerous`;
  - flask: `sudo pip3 install flask`;
  - flask_httpauth: `sudo pip3 install flask_httpauth`;
  - oauth2client: `sudo pip3 install oauth2client`;
  - postgresql:
    - `sudo apt-get install postgresql`;
    - `sudo apt-get install libpq-dev`;
    - `sudo pip3 install psycopg2`.


## Instructions

1 - Get the Linux VM up and access it. Then navigate to the project folder.

2 - Create the PostgreSQL database user:

`sudo su postgres -c "psql -c \"CREATE USER catalog PASSWORD 
'icproject';\""`

3 - Create the database tables:

`python3 database.py`

4 - Populate the database with some example categories initial data:

`python3 populate_db.py`

5 - Make sure you have both Facebook and Google JSON client secrets files 
inside of folder below. It must contain your web app information from developers site:

`static/json`

6 - The Facebook and Google JSON files must have these names:

`facebook_client_secrets.json` and `google_client_secrets.json`

7 - Inside the project folder, run the command below to start the app:

`python3 application.py`

8 - The python commands above must be run in the Linux VM environment and 
inside the project folder.

9 - Now access from your browser the web site:

`http://localhost:5000`


## Design

### Project contents:

#### 1- application.py
The Flask application with routes treatment.

The app will interact with Database through SQLAlchemy. And with oauth providers through project defined functions in oauth_providers module.

#### 2 - database.py
The database module that defines the DB engine and tables models.

When running this module from command line it will create the DB tables. This is necessary for initial DB startup.

At the current version this projects uses PostgreSQL as database.

#### 3 - populate_db.py
Module to populate database with example info.

When running this module from command line it will populate the DB with predefined categories and some example item and user data.

#### 4 - oauth_providers.py
Utility module to provide oauth methods.

It includes:
- connection to third party authentication providers in order to authenticate and get user info;
- disconnection method from providers;
- registering of oauth provider user in database.

#### 5 - HTML templates
The html templates are inside of `/templates` folder.

#### 6 - Static folder
It contains:
- `/css` folder: sytles.css stylesheet;
- `/images` folder: images for index page;
- `/json` folder: where JSON client secrets should be put.