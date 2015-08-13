#!/usr/bin/env python3
# Author: Milan Oberkirch <zvyn@oberkirch.org>

'''
Wraps a program expecting two arguments: -i filename -o filename in a http
server. For security reasons the command name is hardcoded and for laziness
reasons it is hardcoded here:
'''
cmd = 'true'

from flask import Flask, request, abort
from tempfile import NamedTemporaryFile
from subprocess import call

def command_wrapper(cmd, input_file_name, output_file_name):
    return call([cmd, '-i', input_file_name, '-o', output_file_name])


app = Flask(__name__)

@app.route("/", methods = ['POST'])
def process():
    input_file = NamedTemporaryFile(delete=False)
    output_file = NamedTemporaryFile(delete=False)
    input_file.write(request.data)
    input_file.close()

    if command_wrapper(cmd, input_file.name, output_file.name) < 1 or app.debug():
        return output_file.read()
    else:
        abort(500, message="Processing of input data failed.")


if __name__ == "__main__":
    app.debug = True
    app.run()
