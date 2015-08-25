#!/usr/bin/env python3
# Author: Milan Oberkirch <zvyn@oberkirch.org>


'''
Wraps a program expecting two filenames as arguments in a http server. The
output mime-type defaults to the input mime-type if the mime-type setting is
empty. If set in the config, only files of the specified type are accepted
and produced. The configuration file is found by

1. Reading a the path from the INOUTCMD_INI env variable or
2. Looking at './inoutcmd.ini'.

Example configuration:

    [inoutcmd]
    # The URI used to access this API:
    path = /api
    # The wrapped command (use '{infile}' and '{outfile}' instead of actual
    # filenames):
    command = cp {infile} {outfile}
    # Leave blank to allow any file-types or specify one mime-type here:
    mime-type =
'''


try:
    # Python 3
    from configparser import ConfigParser
except:
    # Python 2
    from ConfigParser import ConfigParser

    def getitem_patch(self, section):
        return dict(self.items(section))

    ConfigParser.__getitem__ = getitem_patch


from os import environ
from flask import Flask, request, abort, send_file
from tempfile import mkdtemp
from subprocess import call
from shutil import rmtree
from basic_auth import requires_auth, change_password as ba_change_password


app = Flask(__name__)
config = ConfigParser()
config_file = (
    environ['INOUTCMD_INI'] if 'INOUTCMD_INI' in environ
    else 'inoutcmd.ini')
config.read(config_file)
command = config['inoutcmd']['command']
mime_type = config['inoutcmd']['mime-type']


def command_wrapper(cmd, input_file_name, output_file_name):
    if cmd == '' and app.debug:
        with open(input_file_name, 'r') as input_file:
            input_data = input_file.read()
        with open(output_file_name, 'w') as output_file:
            output_file.write("no command specified, input:\n%s" % input_data)
        return 0
    return call(
        cmd.format(infile=input_file_name, outfile=output_file_name),
        shell=True)


@app.route(config['inoutcmd']['path'], methods=['GET', 'POST'])
@requires_auth
def process():
    if request.method == 'GET':
        if app.debug:
            return config['inoutcmd']['form']
        else:
            abort(403, 'Method not allowed.')

    folder = mkdtemp(prefix=__name__)
    input_file_name = "%s/input_file" % folder
    output_file_name = "%s/output_file" % folder
    content_type = request.headers['Content-Type']

    if content_type[:9] == 'multipart':
        input_file = request.files['input_file']
        content_type = input_file.content_type
        if len(mime_type) and content_type != mime_type:
            abort(409, "Please choose a %s file." % mime_type.split('/').pop())
        input_file.save(input_file_name)
    elif content_type[:4] == 'text':
        with open(input_file_name, 'w') as input_file:
            input_file.write(request.data)
    else:
        abort(409, "Wrong content type.")

    try:
        if command_wrapper(
                command, input_file_name, output_file_name) < 1:
            output_mimetype = mime_type if len(mime_type) else content_type
            return send_file(
                output_file_name,
                as_attachment=True,
                mimetype=output_mimetype,
                attachment_filename=('result.%s' %
                                     output_mimetype.split('/').pop()))
        else:
            abort(500, "Processing of input data failed.")
    finally:
        if not app.debug:
            rmtree(folder)


@app.route(
    '%s/change_password' % config['inoutcmd']['path'],
    methods=['PUT', 'POST'])
@requires_auth
def change_password():
    user = request.authorization.username
    password = request.form['password']
    ba_change_password(user, password)
    return "Password changed successfully!"


if __name__ == "__main__":
    app.debug = True
    app.run()
