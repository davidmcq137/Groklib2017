#!/usr/bin/python

from __future__ import print_function

import datetime
import requests
import os
import ConfigParser
import statsdb
import time
import dothat.lcd as lcd
import dothat.backlight as backlight

from requests.auth import HTTPBasicAuth
from time import sleep
from gpiozero import DigitalInputDevice
#from datadog import statsd


def btoi(v):
    return 1 if v else 0

def send_sms(dest, body, t_user, t_pass, t_num, t_acct):
    timestamp = datetime.datetime.now()
    try:    
        ret_req = requests.post( "https://api.twilio.com/2010-04-01/Accounts/" + 
                    t_acct + "/Messages.json", auth = HTTPBasicAuth(t_user, t_pass),
                    data = {'To':   dest,'From': t_num,'Body': "[" + str(timestamp) + "] " + body})
    except:
         ret_req=-1
         print("Exception calling requests.post")

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



did = DigitalInputDevice(5)

index = 0
jndex = 0
last_st = 0
excount = 0
st = 2
gen_start_time = 0.0
server_address = ('10.0.0.48',10137)

nn = datetime.datetime.now()
lcd.set_contrast(50)
backlight.hue(0.5)
backlight.set_graph(0.0)
lcd.set_cursor_position(0,0)
lcd.write("Monitor Starting")
#          1234567890123456
lcd.set_cursor_position(0,1)
lcd.write(nn.strftime("%a %b %d %H:%M"))
lcd.set_cursor_position(0,2)
lcd.write("                ")
#          1234567890123456

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
            print("Texting [" + str(datetime.datetime.now()) + "] " + "Generator is STARTING")
            body = "Gen is STARTING "
#                   1234567890123456
            lcd.set_cursor_position(0,0)
            lcd.write(body)
            send_sms(dfm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)
   #        send_sms(lrm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)
  
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

    nn = datetime.datetime.now()
    lcd.set_cursor_position(0,0)
    gss = ["OFF", "EXC", "ON "][st]
    # print("st is: ", st)
    # print("gss: ", gss)
    lcd.write("GEN_STATE: " + gss + "  ")
    lcd.set_cursor_position(0,1)
    lcd.write(nn.strftime("%a %b %d %H:%M"))
    backlight.set_graph(index/15.0)

    if index >= 15:
        index=0
        #statsd.gauge("Generator State", gs)
        #print("Calling statsdb", gs)
        statsdb.statsdb("GEN_STATE", gs)


    if last_st != st:

        # print("last != .. st is: ", st)

        if st == 0: # about to say gen is off .. add delta t string
            gen_run_time = time.time() - gen_start_time
            print("Generator run time (s) is: ", gen_run_time)
            gen_off_str = ". Run time (m): {:.2f}".format(gen_run_time/60.0)
            lcd_off_str = "Last (m): {:3.1f}".format(gen_run_time/60.0)
        else:
            lcd_off_str = "                "
#                          1234567890123456
            gen_off_str = ''

        print("Texting [" + str(datetime.datetime.now()) + "] " + 
               "Generator is " + ["OFF", "EXERCISING", "ON"][st] +
               gen_off_str)

        body = "Generator is " + ["OFF", "EXERCISING", "ON"][st] + gen_off_str
        lcd_body = "Generator is " + ["OFF", "EXE", "ON "][st]
#                   Generator is OFF
#                   1234567890123456        
        lcd.set_cursor_position(0,0)
	lcd.write("                ")
#                  1234567890123456
        lcd.set_cursor_position(0,0)
	lcd.write(lcd_body)
        nn=datetime.datetime.now()
        lcd.set_cursor_position(0,1)
        lcd.write(nn.strftime("%a %b %d %H:%M"))
        lcd.set_cursor_position(0,2)
        lcd.write("                ")
#                  1234567890123456
        lcd.set_cursor_position(0,2)
        lcd.write(lcd_off_str)
            

        send_sms(dfm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)
        send_sms(lrm_cell, body, twilio_user, twilio_pass, twilio_num, twilio_acct)

    last_st = st
    sleep(0.2)
    

pass
    
