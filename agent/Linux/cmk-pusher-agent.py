#!/usr/bin/env python3
# This file is part of CMK Pusher.
# Copyright by Markus Plischke and Q-MEX Networks.  All rights reserved.
#
# CMK Pusher is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.
#
# CMK Pusher is  distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# CMK Pusher is a passive push service for Check_MK
#
# @author Markus Plischke <m.plischke@q-mex.net>
# @company Q-MEX Networks https://www.q-mex.net

from subprocess import PIPE, Popen
from configparser import ConfigParser
import zlib
import base64
import sys
import os
import requests

# Config File Path
cfile = str(os.path.dirname(sys.argv[0]))+"/config.ini"

config = ConfigParser()

def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def json_client(action,data):
    d = {}
    d['auth'] = {}
    d['auth']['secret'] = ConfigSectionMap("server")['secret']
    d['transaction'] = {}
    if action == "push":
        d['transaction']['action'] = "push"
        d['transaction']['compress'] = ConfigSectionMap("server")['compress'] == 'True'
        d['transaction']['values'] = data['values']

    srvurl = "https://"+ConfigSectionMap("server")['host']+"/api/json.php"

    resp = requests.post(srvurl, json=d)
    if resp.status_code >= 400:
        print("Error sending data to Check_MK Server")
        print(resp.text)
        sys.exit(1)

try:
    config.read(cfile)
except:
    print("config.ini does not exist")
    sys.exit(1)

command = ConfigSectionMap("check_mk")['path']
process = Popen(command, shell=True, stdout=PIPE).stdout
if process is None:
    print("Process returned no output")
    sys.exit(1)

output = process.read()


if ConfigSectionMap("server")['compress'] == 'True':
    output = base64.b64encode(zlib.compress(output,9))
else:
    output = base64.b64encode(output)

data = {}
data['values'] = {}
data['values']['client_name'] = ConfigSectionMap("check_mk")['client_name']
data['values']['agentoutput'] = output.decode()  # To convert byte-string to string

json_client("push",data)
