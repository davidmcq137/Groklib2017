#!/usr/bin/env python
from __future__ import print_function
import requests
import ConfigParser
import subprocess
import os
import time
import datetime
from requests.auth import HTTPBasicAuth

config=ConfigParser.ConfigParser()
osp = os.path.expanduser('~/twilio.conf')
config.read(osp)

dfm_cell = config.get('PHONES','dfm_cell')

print("Watching read-remotes.py -- will text if it aborts")
print("Will text alerts to: ", dfm_cell)

def send_sms(body, dest):
    
    config=ConfigParser.ConfigParser()
    osp = os.path.expanduser('~/twilio.conf')
    config.read(osp)
    t_acct   = config.get('KEYS', 'twilio_acct')
    t_user   = config.get('KEYS', 'twilio_user')
    t_pass   = config.get('KEYS', 'twilio_pass')
    t_num    = config.get('PHONES' , 'twilio_num')
    dfm_cell = config.get('PHONES'   , 'dfm_cell')
    lrm_cell = config.get('PHONES'   , 'lrm_cell')

    timestamp = datetime.datetime.now()
    
    ret_req = requests.post( "https://api.twilio.com/2010-04-01/Accounts/" + 
                    t_acct + "/Messages.json", auth = HTTPBasicAuth(t_user, t_pass),
                    data = {'To':   dest,'From': t_num,'Body': "[" + str(timestamp) + "] " + body})

    #print("Requests returns: ", ret_req)
    print("send_sms:[" + str(timestamp) + "] sent \"" + body + "\" to "+dest)
    return ret_req

watch_running = True # start by assuming its running

while True:
    process='read-remotes.py'

    ps_out = subprocess.check_output(["ps", "aux"])

#    print("ps_out: ", ps_out)
    
    if not (process in ps_out) and watch_running:
        print("Process has stopped: ", process)
        # put sms call here
        body_str = "Process " + process + " has stopped."
        ret_sms = send_sms(body_str, dfm_cell)
        # only want to send this message once, will reset if process restarts
        watch_running = False

    if (process in ps_out) and (not watch_running):
        print("Process has restarted: ", process)
        # put sms call here?
        body_str = "Process " + process + " has restarted."
        ret_sms = send_sms(body_str, dfm_cell)
        watch_running = True

    time.sleep(120)
    
