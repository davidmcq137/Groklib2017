#!/usr/bin/env python

from __future__ import print_function

import datetime
import requests
import ConfigParser
from requests.auth import HTTPBasicAuth

# function to send out an SMS message. assumes you have all the secrets on-hand

def send_sms(dest, body, t_user, t_pass, t_num, t_acct):
    timestamp = datetime.datetime.now()
    
    ret_req = requests.post( "https://api.twilio.com/2010-04-01/Accounts/" + 
                    t_acct + "/Messages.json", auth = HTTPBasicAuth(t_user, t_pass),
                    data = {'To':   dest,'From': t_num,'Body': "[" + str(timestamp) + "] " + body})
    print("Requests returns: ", ret_req)
    print("send_sms:[" + str(timestamp) + "] sent \"" + body + "\" to "+dest)

# function to get the secrets from the config file
# returns a monster named tuple with the relevant info
# assumes the secrets are in the parent director, presuming the working director is public via gh

def get_sms_secrets():
    
    config=ConfigParser.ConfigParser()
    osp = os.path.expanduser('~/twilio.conf')

    config.read(osp)

    acct = config.get('KEYS', 'twilio_acct')
    user = config.get('KEYS', 'twilio_user')
    pswd = config.get('KEYS', 'twilio_pass')

    num  = config.get('PHONES' , 'twilio_num')
    dfm_cell    = config.get('PHONES'   , 'dfm_cell')
    lrm_cell    = config.get('PHONES'   , 'lrm_cell')

    return t_secrets(acct, user, pswd, num, dfm_cell, lrm_cell)

