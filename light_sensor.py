#!/usr/bin/python3
import datetime
import requests
import os
from requests.auth import HTTPBasicAuth
from gpiozero import LEDBarGraph
from time import sleep
from gpiozero import DigitalInputDevice

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
graph = LEDBarGraph(27, 26, 25, 24, 23, pwm=True)

off_threshold = 0.75
on_threshold = 0.95

old = 1
nv = 1
st = 1
tau = 10.0
delta = 0.0

print("Startup: [" + str(datetime.datetime.now()) + "] UTC")

while True:

    val = did.value
    delta = btoi(val)-old
    
    if delta < 0.0:
         tau=3.0
    else:
         tau=20.0
         
    nv = delta/tau + old

    if nv < 0.01:
        nv = 0.01
    elif nv > 0.99:
        nv = 0.99

    #if (nv > off_threshold/10.) and (nv < on_threshold):
    #    print("{:0.2f}".format(nv))

    graph.value = nv

    last_st = st
    if nv < old and nv < off_threshold:
        st = 0
    elif nv > old and nv > on_threshold:
        st = 1
    if last_st != st:
        print("[" + str(datetime.datetime.now()) + "] UTC. Input = " + "{:0.2f}".format(nv) + "% Generator is " + ["ON", "OFF"][st])
        body = "generator is " + ["ON", "OFF"][st]
        send_sms(os.environ['DFM_CELL'], body)
        send_sms(os.environ['LRM_CELL'], body)
        
    sleep(0.2)
    old = nv

    
