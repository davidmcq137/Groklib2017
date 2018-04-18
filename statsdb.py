#!/usr/bin/env python
from __future__ import print_function
import socket
import time
import os
import platform
import copy
import ConfigParser
import requests
import datetime
from requests.auth import HTTPBasicAuth

server_address = ('10.0.0.48',10137)

def statsdb(channel, value):
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        pyname = os.path.basename(__file__)
        sockpayload = (channel + "," + str(int(time.time())) + ","
                       + str(value) + ",DD" + "," + platform.node())
        # print("sockpayload: ", sockpayload)
        sock.sendall(sockpayload)
    except:
        print ("Exception calling sock.sendall at [" + str(int(time.time())) + "]")
    finally:
        sock.close()

    return

def write_channels(x_dict, c_dict, prt=False, sdb=True, div=1.0):
    #cc_dict=copy.deepcopy(c_dict) # no longer needed with mod to read_nested_dict to not use pop()
    rt = 0.0
    for c,l in c_dict.iteritems():
        s = str(read_nested_dict(x_dict, l))
        if s != 'None':
            r = float(s)/div
            rt = rt + r
            v = str(r)
        else:
            v = 'None'
        if prt: print(c + ': ' + v)
        if sdb: statsdb(c,v)
    return(rt)
                        
def read_nested_dict(in_dict, keylist):
    firstkey = keylist[0]
    if type(in_dict) == list and type(keylist[0]) == int:
        idgf = in_dict[firstkey]
    else:
        idgf = in_dict.get(firstkey)
    if idgf == None: return (None)
    if len(keylist[1:]) > 0:
        return(read_nested_dict(idgf, keylist[1:]))
    else:
        return(idgf)


def send_sms_ltd(body, dest_in):
    
    config=ConfigParser.ConfigParser()
    osp = os.path.expanduser('~/twilio.conf')
    config.read(osp)
    t_acct   = config.get('KEYS', 'twilio_acct')
    t_user   = config.get('KEYS', 'twilio_user')
    t_pass   = config.get('KEYS', 'twilio_pass')
    t_num    = config.get('PHONES' , 'twilio_num')
    dfm_cell = config.get('PHONES'   , 'dfm_cell')
    lrm_cell = config.get('PHONES'   , 'lrm_cell')

    if dest_in == 'dfm_cell':
        dest = dfm_cell
    elif dest_in == 'lrm_cell':
        dest = lrm_cell
    else:
        return(-1)
    
    timestamp = datetime.datetime.now()
    print("About to send_sms:[" + str(timestamp) + "] sent \"" + body + "\" to " + dest)
    
    try:
        ret_req = requests.post( "https://api.twilio.com/2010-04-01/Accounts/" + 
                    t_acct + "/Messages.json", auth = HTTPBasicAuth(t_user, t_pass),
                    data = {'To':   dest,'From': t_num,'Body': "[" + str(timestamp) + "] " + body},
                    timeout=2.0)
    except requests.exceptions.ConnectionError :
        print('ConnectionError exception in Twilio API call: ' + str(sys.exc_info()[0]) +
              ' ['+str(datetime.datetime.now())+']' )
        ret_req = -1
        
    #print("Requests returns: ", ret_req)

    return ret_req
