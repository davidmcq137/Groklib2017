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

ipoll = 0

with open('/tmp/read-ted.py.pid', 'w') as f:
    f.write(str(os.getpid()))

link="http://10.0.0.41/api/LiveData.xml"

while True:    

    while True:
        ipoll = ipoll + 1
        print("Polling TED at: " + str(datetime.datetime.now()))
        try:
            rc = requests.get(link, timeout=2.0)
            ted_api_dict = xmltodict.parse(rc.text)
            ipoll = 0
            break
        except:
            print("Exception on request to TED: " + str(sys.exc_info()[0]) +' ['+ str(datetime.datetime.now())+']' )
            print("Return code from requests.get: ", rc.status_code)
            sys.stdout.flush()
            if ipoll > 100:
                print("Too many read errors on TED: exiting")
                exit()
            else:
                time.sleep(10)
            

    voltage_now = float(ted_api_dict['LiveData']['Voltage']['Total']['VoltageNow'])/10.0
    power_now   = float(ted_api_dict['LiveData']['Power']['Total']['PowerNow'])

    print('VoltageNow: ', voltage_now)
    print('PowerNow: ', power_now)
    
    statsdb.statsdb('Voltage', voltage_now)
    statsdb.statsdb('Power', power_now)


    sys.stdout.flush()
    time.sleep(30)




