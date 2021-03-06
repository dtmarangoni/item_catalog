#!/usr/bin/env python3
#
"""The database module that defines the DB engine and tables models.

When running this module from command line it will create the DB
tables. This is necessary for initial DB startup.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from passlib.apps import custom_app_context as pswd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          BadSignature, SignatureExpired)
import random
import string


# Create the DB engine and session
# engine = create_engine('sqlite:///item_catalog.db', convert_unicode=True)
engine = create_engine(
    'postgresql://catalog:icproject@localhost:5432/item_catalog',
    convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

# Using secrets module only available on Python 3.6 or above
# state = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
#                for _ in range(32))
secret_key = ''.join(random.SystemRandom().choice(
    string.ascii_uppercase + string.digits) for _ in range(32))


class User(Base):
    """Class that represents the user table in DB.

    It also has methods for hashing and verifying user password, and
    generating and validating authentication tokens.
    """

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), nullable=False)
    password_hash = Column(String())
    email = Column(String(60), nullable=False, unique=True, index=True)
    picture = Column(String(250))
    provider = Column(String(32))
    oauth_user_id = Column(String(32))
    oauth_token = Column(String())

    def hash_password(self, password):
        """Hash the user password and stores in password_hash attribute.

        Args:
            password (str): the user password.
        """
        self.password_hash = pswd_context.hash(password)

    def verify_password(self, password):
        """Verify if the password matches with the hashed attribute.

        Args:
            password (str): the user password to be verified.

        Returns:
            bool: True for success, False otherwise.
        """
        return pswd_context.verify(password, self.password_hash)

    def gen_auth_token(self, expiration=600):
        """Generate an authentication token.

        Args:
            expiration (int): the token expiration time in seconds.
            Default value is 600.

        Returns:
            json: The authentication token with a JSON Web Signature and
            optional added headers.
        """
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        """Verify if the authentication token is valid.

        Args:
            token (str): the authentication token.

        Returns:
            None: if the token is expired or invalid.
            id (int): the user id.
        """
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # Valid token but expired
            return None
        except BadSignature:
            # Invalid token
            return None
        return data['id']

    @property
    def serialize(self):
        """Send a JSON object in a serializable format.

        Returns: the JSON object.
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'picture:': self.picture
        }


class Category(Base):
    """Class that represents the item category in DB.

    It can be serializable.
    """

    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, index=True, unique=True)

    @property
    def serialize(self):
        """Send a JSON object in a serializable format.

        Returns: the JSON object.
        """
        return {
            'id': self.id,
            'name': self.name
        }


class Item(Base):
    """Class that represents the item in DB.

    It can be serializable.
    """

    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500))
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship(
        Category, backref=backref('category', cascade="all, delete-orphan"))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)

    @property
    def serialize(self):
        """Send a JSON object in a serializable format.

        Returns: the JSON object.
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'user_id': self.user_id
        }


def init_db():
    """Create the DB tables.

    This is necessary as initial step of app installation.
    """
    Base.metadata.create_all(bind=engine)


# When running this module from command line it will create the DB tables.
# This is necessary for initial DB startup.
if __name__ == '__main__':
    """When running this module from command line it will create the DB tables.

    This is necessary for initial DB startup.
    """
    init_db()
