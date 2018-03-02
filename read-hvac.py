#!/usr/bin/python

from __future__ import print_function

import datetime
import statsdb
import time
from time import sleep
from gpiozero import DigitalInputDevice

def btoi(v):
    return 0 if v else 1

# Initialize the RPi digital I/O ports as digital inputs

did21 = DigitalInputDevice(21)
did20 = DigitalInputDevice(20)
did16 = DigitalInputDevice(16)
did12 = DigitalInputDevice(12)

did25 = DigitalInputDevice(25)
did24 = DigitalInputDevice(24)
did8  = DigitalInputDevice(8)
did7 =  DigitalInputDevice(7)

didvals = {did21:0, did20:0, did16:0, did12:0, did25:0, did24:0, did8:0, did7:0}

didname = {did21:'USPowerWire',  # Red (now 24V "hot" to be changed to Mode)
           did20:'USEmergWire',  # White
           did16:'USFanWire',    # Green
           did12:'USHeatACWire', # Yellow
           did25:'DSFanWire',    # Green
           did24:'DSHeatACWire', # Yellow
           did8: 'DSEmergWire',  # White
           did7: 'DSModeWire' }  # Red (really should be an orange wire)


while True:

    # First sample about 1 secs of data, 120 samples spaced by 1/120 sec
    # btoi() changes on/off to 0 and 1 so just add up the samples

    for i in range(120):

        for k in didvals:
            val = btoi(k.value)
            didvals[k] = didvals[k] + val
        time.sleep(0.0083)

    # Now normalize the results. If signal on (24VAC) expect half-wave rectified 60 Hz sinewave
    # with avg val of about 0.5 ... set on/off threshold at half of that or 0.25
    # write out the samples to statsdb

    print("Wire status at: ", datetime.datetime.now())

    for k in didvals:
        didvals[k] = didvals[k]/120.0
        if didvals[k] < 0.25:
            didvals[k] = 0.0
        else:
            didvals[k] = 1.0
        print(didname[k], didvals[k])
        statsdb.statsdb(didname[k], didvals[k])
    time.sleep(30)
pass

