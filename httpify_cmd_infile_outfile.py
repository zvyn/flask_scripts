#!/usr/bin/env python3
# Author: Milan Oberkirch <zvyn@oberkirch.org>

'''
Wraps a program expecting two arguments: -i filename -o filename in a http
server. For security reasons the command name is hardcoded and for laziness
reasons it is hardcoded here:
'''
cmd = ''

# quick and dirty:
form = '''
<!DOCTYPE html>

<head><title>this is valid html5</title></head>
<body>
    <form method="POST" action="http://localhost:5000/" enctype="multipart/form-data">
        <input type="FILE" name="input_file">
        <input type="SUBMIT">
    </form>
</body>
'''

from flask import Flask, request, abort
from tempfile import mkdtemp
from subprocess import call
from shutil import rmtree


app = Flask(__name__)


def command_wrapper(cmd, input_file_name, output_file_name):
    if cmd == '' and app.debug:
        with open(input_file_name, 'r') as input_file:
            input_data = input_file.read()
        with open(output_file_name, 'w') as output_file:
            output_file.write("no command specified, input:\n%s" % input_data)
        return 0
    return call([cmd, '-i', input_file_name, '-o', output_file_name])


@app.route("/", methods = ['GET', 'POST'])
def process():
    if request.method == 'GET':
        return form

    folder = mkdtemp(prefix=__name__)
    input_file_name = "%s/input_file" % folder
    output_file_name = "%s/output_file" % folder

    if request.headers['Content-Type'][:9] in 'multipart':
        input_file = request.files['input_file']
        input_file.save(input_file_name)
    elif request.headers['Content-Type'][:4] == 'text':
        with open(input_file_name, 'w') as input_file:
            input_file.write(request.data)
    else:
        abort(409, "Wrong content type.")

    try:
        if command_wrapper(cmd, input_file_name, output_file_name) < 1 or app.debug:
            with open(output_file_name, 'r') as output_file:
                return output_file.read()
        else:
            abort(500, "Processing of input data failed.")
    finally:
        rmtree(folder)


if __name__ == "__main__":
    app.debug = True
    app.run()
