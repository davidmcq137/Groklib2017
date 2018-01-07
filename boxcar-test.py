#!/usr/bin/python
import datetime
import requests
import os
from requests.auth import HTTPBasicAuth
from gpiozero import LEDBarGraph
from time import sleep
from gpiozero import DigitalInputDevice
from datadog import statsd

def btoi(v):
    return 1 if v else 0

def send_sms(dest, body):
    timestamp = datetime.datetime.now()
    requests.post("https://api.twilio.com/2010-04-01/Accounts/" + os.environ['TWILIO_ACCT'] + "/Messages.json",
                  auth = HTTPBasicAuth(os.environ['TWILIO_USER'], os.environ['TWILIO_PASS']),
                  data = {'To':   dest,
                          'From': os.environ['TWILIO_NUM'],
                          'Body': "[" + str(timestamp) + "] " + body})
    print("[" + str(timestamp) + "] sent \"" + body + "\" to "+dest)

did = DigitalInputDevice(18)

index = 0
jndex = 0
last_st = 0
excount = 0
st = 2

print("Startup: [" + str(datetime.datetime.now()) + "]")

while True:

# First sample about 4 secs of data, 20 samples spaced by 200ms

 #  print("Taking 20 samples, 200msec apart")
    sigma=0   
    for i in range(20):
        val = btoi(did.value)

        if (st == 0) & (val == 0):  #Gen was off, but signal is on, it must be starting .. send message right away
            st = 2 # don't trigger again this loop of 20
            print("Would be Texting [" + str(datetime.datetime.now()) + "] " + "(B)Generator is STARTING")

            body = "(B)Generator is STARTING"
            send_sms(os.environ['DFM_CELL'], body)
            send_sms(os.environ['LRM_CELL'], body)
  
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

# only feed statsd every 4 sec * 15 = 60 seconds, that lets us do a lost data monitor on it to see if monitor is down

    if index >= 15:
        index=0
  #     print("Calling statsd.gauge with gs= ", str(gs))
        statsd.gauge("Generator State", gs)

    if last_st != st:
        print("Would be texting [" + str(datetime.datetime.now()) + "] " + 
               "(B)Generator is " + ["OFF", "EXERCISING", "ON"][st])

        body = "(B)Generator is " + ["OFF", "EXERCISING", "ON"][st]
        send_sms(os.environ['DFM_CELL'], body)
        send_sms(os.environ['LRM_CELL'], body)

    last_st = st
    sleep(0.2)
    

pass
    
