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

off_threshold = 0.2
on_threshold = 0.8

old = 1
nv = 1
st = 1

while True:
    val = did.value
    nv = (btoi(val) - old)/10.0 + old
    if nv < 0.10:
        nv = 0.10
    elif nv > 0.90:
        nv = 0.90
    else:
        print("[" + str(datetime.datetime.now()) + "] " + "%0.2f".formav(nv))

    graph.value = nv

    last_st = st
    if nv < old and nv < off_threshold:
        st = 0
    elif nv > old and nv > on_threshold:
        st = 1
    if last_st != st:
        body = "generator is " + ["ON", "OFF"][st]
        send_sms(os.environ['DFM_CELL'], body)
        send_sms(os.environ['LRM_CELL'], body)
        
    sleep(0.5)
    old = nv

    
