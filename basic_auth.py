#!/usr/bin/env python3
# Author: Milan Oberkirch <zvyn@oberkirch.org>


"""
Provides a `requires_auth` decorator which enables basic auth for the decorated
function by checking for config section called username and an entry
password_hash. If the lookup fails or the hmac hash of the given password is
not equivalent to the one in the `config_file`, the authentication fails and a
401 response is sent to the client.
"""


from os import environ
from passlib.hash import sha256_crypt as pwhash

try:
    # Python 3
    from configparser import ConfigParser
except:
    # Python 2
    from ConfigParser import ConfigParser

    def getitem_patch(self, section):
        return dict(self.items(section))

    def setitem_patch(self, section, values):
        for k, v in values.items():
            self.set(section, k, v)

    ConfigParser.__getitem__ = getitem_patch
    ConfigParser.__setitem__ = setitem_patch

from functools import wraps
from flask import request, Response


config = ConfigParser()
config_file = (
    environ['BASIC_AUTH_INI'] if 'BASIC_AUTH_INI' in environ
    else 'basic_auth.ini')
config.read(config_file)


def check_auth(username, password):
    """
    Check user and password.
    """
    try:
        password_hash = config[username]["password_hash"]
        return pwhash.verify(password, password_hash)
    except KeyError:
        return False


def authenticate():
    return Response(
        'Please log in to use this service.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def change_password(username, new_password):
    config[username] = {'password_hash': pwhash.encrypt(new_password)}
    with open(config_file, 'w') as f:
        config.write(f)

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    @requires_auth
    def secret():
        return "Hello World!"

    app.debug = True
    app.run()
