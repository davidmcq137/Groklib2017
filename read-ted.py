#!/usr/bin/env python
from __future__ import print_function
from __future__ import with_statement

import requests
import re
import os
import time
import sys
import datetime
#from datadog import statsd
import statsdb
import xmltodict


def read_spyder(slist):

    url_left  = 'http://10.0.0.35/history/export.csv?T=1&D=1&M='
    url_right = '&C=1'
    ret_dict={}

    for sp in slist:
        url=url_left + '{:d}'.format(sp) + url_right
        rc = poll_ted(url)
        lines=rc.text.splitlines()
        vals =lines[1].split(',')
        chan = 'SP-' + vals[0]
        pwr=vals[2]
        ret_dict[chan]=pwr

    return ret_dict

def poll_ted(link):
    ipoll = 0
    while True:
        ipoll = ipoll + 1
        if ipoll > 1:
            print("Iterating TED poll#: ", ipoll)
        try:
            rcc = requests.get(link, timeout=2.0)
            ipoll = 0
            break
        except:
            print("Exception on request to TED: " +
                  str(sys.exc_info()[0]) +' ['+ str(datetime.datetime.now())+']' )
            sys.stdout.flush()
            if ipoll > 1000:
                print("Too many read errors on TED: exiting")
                exit()
            else:
                time.sleep(10)
    return rcc
    
with open('/tmp/read-ted.py.pid', 'w') as f:
    f.write(str(os.getpid()))

sys_ovr="http://10.0.0.35/api/SystemOverview.xml?T=0"

chan_volt={'VoltageLeft' :['DialDataDetail', 'MTUVal', 'MTU1', 'Voltage'],
           'VoltageRight':['DialDataDetail', 'MTUVal', 'MTU2', 'Voltage']}

chan_pwr ={'PowerLeft '  :['DialDataDetail', 'MTUVal', 'MTU1', 'Value'],
           'PowerRight'  :['DialDataDetail', 'MTUVal', 'MTU2', 'Value'] }

# spy_list: list of connected spyders. 1-8 on MTU1, 9-16 on MTU2
# channel names are set in the Footprints tool, pre-pended with "SP-" here

spy_list=[1,2,3,4,5,6,7,9,10,11,12,13,14,15]


while True:
    
    print("Polling TED at: " + str(datetime.datetime.now()))

    rc = poll_ted(sys_ovr)
    ted_api_dict = xmltodict.parse(rc.text)

    statsdb.write_channels(ted_api_dict, chan_volt, prt=False, sdb=True, div=10.0)
    pp = statsdb.write_channels(ted_api_dict, chan_pwr , prt=False, sdb=True, div=1.0)
    #print('Power: ', pp) # special feature: return code is sum of channel values
    statsdb.statsdb('Power', pp)
    
    d = read_spyder(spy_list)

    for kk, vv  in d.iteritems():
        #print(kk, vv)
        statsdb.statsdb(kk, vv)
        

    sys.stdout.flush()
    time.sleep(60)




