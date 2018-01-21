#!/usr/bin/python

from __future__ import print_function

import datetime
import requests
import os
import ConfigParser
import statsdb
import time

from requests.auth import HTTPBasicAuth
from time import sleep
from gpiozero import DigitalInputDevice
#from datadog import statsd


def btoi(v):
    return 1 if v else 0

def send_sms(dest, body, t_user, t_pass, t_num, t_acct):
    timestamp = datetime.datetime.now()
    
    ret_req = requests.post( "https://api.twilio.com/2010-04-01/Accounts/" + 
                    t_acct + "/Messages.json", auth = HTTPBasicAuth(t_user, t_pass),
                    data = {'To':   dest,'From': t_num,'Body': "[" + str(timestamp) + "] " + body})
    print("Requests returns: ", ret_req)
    print("send_sms:[" + str(timestamp) + "] sent \"" + body + "\" to "+dest)

# Get the secrets from the config file

config=ConfigParser.ConfigParser()
osp = os.path.expanduser('~/twilio.conf')

config.read(osp)

twilio_acct = config.get('KEYS', 'twilio_acct')
twilio_user = config.get('KEYS', 'twilio_user')
twilio_pass = config.get('KEYS', 'twilio_pass')

twilio_num  = config.get('PHONES' , 'twilio_num')
dfm_cell    = config.get('PHONES'   , 'dfm_cell')
lrm_cell    = config.get('PHONES'   , 'lrm_cell')

print("twilio acct: ", twilio_acct)
print("twilio user: ", twilio_user)
print("twilio pass: ", twilio_pass)
print("twilio num:  ", twilio_num )

print("dfm_cell:  ", dfm_cell)
print("lrm_cell:  ", lrm_cell)



did = DigitalInputDevice(18)

index = 0
jndex = 0
last_st = 0
excount = 0
st = 2
gen_start_time = 0.0
server_address = ('10.0.0.48',10137)

print("Startup: about to send text to DFM cell [" + str(datetime.datetime.now()) + "]")

body = "Generator monitor program launching"
send_sms(dfm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)

print("Text sent, beginning light sample loop")

while True:

# First sample about 4 secs of data, 20 samples spaced by 200ms

 #  print("Taking 20 samples, 200msec apart")
    sigma=0   
    for i in range(20):
        val = btoi(did.value)

        if (st == 0) & (val == 0):  #Gen was off, but signal is on, it must be starting .. send message right away
            st = 2 # don't trigger again this loop of 20
            gen_start_time = time.time()
            print("Texting [" + str(datetime.datetime.now()) + "] " + "(B)Generator is STARTING")
            body = "(B)Generator is STARTING"
            send_sms(dfm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)
            send_sms(lrm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)
  
        sigma=sigma+val
        sleep(0.200)

# Normalize it to the boxcar avg value

    Nsigma = sigma/20.0
#   print ("Average value is: "+str(Nsigma))

#   Nsigma = input("Enter hand-insert value for Nsigma: ")
    
# if one sample differs from the others, it's off by 1/20 (0.5), so make sure it's stable 1 or 0 to be OFF or ON
# if somewhere in between, count a second set of 20 samples to see if it's really exercising

    if Nsigma>=0.99:   #Gen is off for sure
        st  = 0
        gs = 0.0
        excount = 0
    elif Nsigma<=0.01: #Gen is on for sure
        st  = 2
        gs = 0.5
        excount = 0
    else:              #Gen is (maybe) exercising - count a few intervals
        excount = excount + 1
        if excount >= 2:
            st  = 1
            excount = 0 #added this line to stop double start message 
        else:
             st = 1 # changed this from last_st .. if not sure, move from 0 to 1 
         
        gs = 0.25  # to see if it's flashing for exercise or on the way to starting
      
    index=index+1

# Only feed statsd every 4 sec * 15 = 60 seconds
# that lets us do a lost data monitor on it to see if monitor is down

    if index >= 15:
        index=0
        #statsd.gauge("Generator State", gs)
        #print("Calling statsdb", gs)
        statsdb.statsdb("GEN_STATE", gs)

    if last_st != st:

        print("st is: ", st)

        if st == 0: # about to say gen is off .. add delta t string
            gen_run_time = time.time() - gen_start_time
            print("Generator run time (s) is: ", gen_run_time)
            gen_off_str = ". Run time (m): {:.2f}".format(gen_run_time/60.0)
        else:
            gen_off_str = ''
            
        print("Texting [" + str(datetime.datetime.now()) + "] " + 
               "Generator is " + ["OFF", "EXERCISING", "ON"][st] +
               gen_off_str)

        body = "Generator is " + ["OFF", "EXERCISING", "ON"][st] + gen_off_str
        send_sms(dfm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)
        if st == 0: # only send LRM starting and ending messages
            send_sms(lrm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)

    last_st = st
    sleep(0.2)
    

pass
    
