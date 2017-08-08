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
import time
import struct
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import logging

TCP_IP = '127.0.0.1'
TCP_PORT = 6556

logging.basicConfig(
    filename = "C:\Install\cmk-pusher-agent\cmk-pusher-agent.log",
    level = logging.DEBUG, 
    format = '[cmk-pusher-agent] %(levelname)-7.7s %(message)s'
)

# Config File Path
cfile = "C:\Install\cmk-pusher-agent\config.ini"
exitFlag = False
logging.info("Loading config file: "+str(cfile))

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
        logging.error("Could not connect to server " + ConfigSectionMap("server")['host'])
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
def recv_timeout(the_socket,timeout=60):
    the_socket.setblocking(0)
     
    total_data=[]
    data=''
     
    begin=time.time()
    while 1:
        if total_data and time.time()-begin > timeout:
            break
        elif time.time()-begin > timeout*2:
            break
         
        try:
            data = the_socket.recv(8192)
            if data:
                total_data.append(data)
                begin=time.time()
            else:
                time.sleep(0.1)
        except:
            pass
     
    return ''.join(total_data)

try:
    config.read(cfile)
except:
    print "config.ini not existing"
    sys.exit(1)

class CMKPService (win32serviceutil.ServiceFramework):
    _svc_name_ = "CMK Pusher"
    _svc_display_name_ = "CMK Push Service"
    _svc_description_ = "Windows Push Service for Check_MK"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.stop_event = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False

    def SvcStop(self):
        global exitFlag
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        exitFlag = True
        win32event.SetEvent(self.stop_event)
        logging.info('Stopping service NOW ...')
        self.stop_requested = True

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_,'')
        )
        self.main()

    def main(self):
        global exitFlag
        logging.info(' ** Starting actions ** ')
        while not exitFlag:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connected = True
                logging.debug("Socket Created")
            except socket.error:
                logging.error("Failed to create socket")
                connected = False
            if connected:
                try:
                    s.connect((TCP_IP , TCP_PORT))
                    connected = True
                    logging.debug("Socket Connected to " + str(TCP_IP) + " on ip " + str(TCP_PORT))
                except:
                    logging.error("Failed to connect")
                    connected = False
            if connected:
                output = recv_timeout(s)
                s.close()
                
                logging.debug(str(output))

                if ConfigSectionMap("server")['compress']:
                    output = base64.b64encode(zlib.compress(output,9))
                else:
                    output = base64.b64encode(output)

                data = {}
                data['values'] = {}
                data['values']['client_name'] = ConfigSectionMap("check_mk")['client_name']
                data['values']['agentoutput'] = output

                json_client("push",data)
                logging.debug("Sending Data to Check_MK Server at %s" % time.ctime())
            time.sleep(55)
        logging.info('Service stopped')
        return

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CMKPService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(CMKPService)
