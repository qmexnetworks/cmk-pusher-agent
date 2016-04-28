#!/usr/bin/python2.7
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
# @company Q-MEX Networks http://www.q-mex.net

import pycurl
import subprocess
import ConfigParser
import zlib
import base64
import json
import StringIO
import sys
import os

# Config File Path
cfile = str(os.path.dirname(sys.argv[0]))+"config.ini"

config = ConfigParser.ConfigParser()

def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
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
        d['transaction']['compress'] = ConfigSectionMap("server")['compress']
        d['transaction']['values'] = data['values']
    jsonarray = json.dumps(d)
    curl = pycurl.Curl()
    srvurl = "https://"+ConfigSectionMap("server")['host']+"/api/json.php"
    curl.setopt(pycurl.URL, srvurl)
    curl.setopt(pycurl.FOLLOWLOCATION, 1)
    contents = StringIO.StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, contents.write)
    curl.setopt(pycurl.VERBOSE, 0)
    curl.setopt(pycurl.POST, 0)
    curl.setopt(pycurl.POSTFIELDS, jsonarray)
    curl.setopt(pycurl.SSL_VERIFYPEER, 0)
    iserror = False
    try:
        curl.perform()
    except:
        print "Could not connect to server " + ConfigSectionMap("server")['host']+"\n"
        iserror = True
    if not iserror:
        curl.close()
        message = contents.getvalue()
        try:
            array = json.loads(message)
        except:
            array = {}
            array['status'] = "error"
            array['message'] = message
        return array
    else:
        return 0

try:
    config.read(cfile)
except:
    print "config.ini not existing"
    sys.exit(1)

command = ConfigSectionMap("check_mk")['path']
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout
output = process.read()


if ConfigSectionMap("server")['compress']:
    output = base64.b64encode(zlib.compress(output,9))
else:
    output = base64.b64encode(output)

data = {}
data['values'] = {}
data['values']['client_name'] = ConfigSectionMap("check_mk")['client_name']
data['values']['agentoutput'] = output

json_client("push",data)