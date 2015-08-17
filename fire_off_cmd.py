#!/usr/bin/env python3
# Author: Milan Oberkirch <zvyn@oberkirch.org>

from flask import Flask, request, abort
from subprocess import call
from os import environ, chdir


app = Flask(__name__)


@app.route("/", methods=['GET'])
def process():
    chdir(flask_root)
    try:
        if request.headers[challenge_header] == challenge_value:
            # Thats obviously dumb, but good enough for my use-case:
            call(flask_command.split(' '))
            return "It's building... ...hopefully.\n"
    except KeyError:
        pass

    return abort(403, "No permissions granted.")


if __name__ == "__main__":
    challenge_header = environ['CHALLENGE_HEADER']
    challenge_value = environ['CHALLENGE_VALUE']
    flask_root = environ['FLASK_ROOT']
    flask_command = environ['FLASK_COMMAND']
    app.run(host='0.0.0.0')
