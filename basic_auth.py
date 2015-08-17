from crypt import crypt
from hmac import compare_digest as compare_hash
from configparser import ConfigParser
from functools import wraps
from flask import request, Response


config = ConfigParser()
config_file = 'basic_auth.ini'
config.read(config_file)


def check_auth(username, password):
    """
    Check user and password using hmac.
    """
    try:
        password_hash = config[username]["password_hash"]
        return compare_hash(password_hash, crypt(password, password_hash))
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
    config[username] = crypt(new_password)
    config.write(config_file)

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    @requires_auth
    def secret():
        return "Hello World!"

    app.debug = True
    app.run()
