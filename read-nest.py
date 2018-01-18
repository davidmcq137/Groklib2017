#!/usr/bin/env python
from __future__ import print_function

import nest
import sys
#from datadog import statsd
import time
import datetime
import ConfigParser
import os
import statsdb

DS_POWER = 5970.0
US_POWER = 6550.0
BS_POWER = 10800.0
AVG_EST_POWER = 0.0
LAST_DS = 0.0
LAST_US = 0.0
ds_rising_time = 0.0
ds_period = 0.0
ds_high_time = 0.0
ds_duty_cycle = 0.0
us_rising_time = 0.0
us_period = 0.0
us_high_time = 0.0
us_duty_cycle = 0.0

with open('/tmp/read-nest.py.pid', 'w') as f:
    f.write(str(os.getpid()))

# set up a ring buffer for power samples. this prog's main loop is 20 seconds, so 3/min, 180/hr

iring = 0                            # average power ring buffer index cycles 0 .. RING_SIZE-1
jring = 0                            # index that goes from 0 to RING_SIZE-1 and stays ther
RING_SIZE = 1080                     # 6 hours
power_sample = [0.0]                 # declare list, set 0th element, elements added as we go


print('Nest Monitor starting up:['+str(datetime.datetime.now())+']')
print("Reading ~/read-nest.conf")

config=ConfigParser.ConfigParser()
osp = os.path.expanduser('~/read-nest.conf')

config.read(osp)

client_id = config.get('KEYS', 'client_id')
client_secret = config.get('KEYS', 'client_secret')

print("Client ID:", client_id)
print("Client Secret: ", client_secret)

access_token_cache_file = os.path.expanduser('~/nest.json')

napi = nest.Nest(client_id=client_id, client_secret=client_secret,
                 access_token_cache_file=access_token_cache_file)

if napi.authorization_required:
    print('Go to: ')
    print(napi.authorize_url)
    print(' to authorize, then enter PIN below')
    if sys.version_info[0] < 3:
        pin = raw_input("PIN: ")
    else:
        pin = input("PIN: ")
    napi.request_token(pin)

for structure in napi.structures:
    print ('Structure name %s' % structure.name)
    print ('Home/Away Status: %s' % structure.away)
    print ('NEST Device Summary:')

    for device in structure.thermostats:
        print ('Device: %s' % device.name)
        print ('Temp: %0.1f' % device.temperature)



while True:
    try:
        for structure in napi.structures:
            for device in structure.thermostats:
                # print(device.name)
                if (device.name=='Downstairs'):
                    if (str(device.hvac_state) == 'heating'):
                         DS_HVAC_STATE = 1.0
                    else:
                         DS_HVAC_STATE = 0.1

                    DS_TEMP = device.temperature
                    DS_HUM = device.humidity
                    DS_TARGET = device.target                                                 

# For Downstairs (one device), it's just 0 or 1
# For Upstairs (three devices), it's 0 or 1.1, 1.2, 1.3

                if (device.name=='Master Bedroom'):
                    if (str(device.hvac_state) == 'heating'):
                        MB_HVAC_STATE = 0.1
                    else:
                        MB_HVAC_STATE = 0.0
                    MB_TEMP = device.temperature
                    MB_HUM = device.humidity
                    MB_TARGET = device.target                        

                if (device.name=='Upstairs'):
                   if (str(device.hvac_state) == 'heating'):
                       UP_HVAC_STATE = 0.1
                   else:
                       UP_HVAC_STATE = 0.0
                if (device.name=='Studio'):
                    if (str(device.hvac_state) == 'heating'):
                        ST_HVAC_STATE = 0.1
                    else:
                        ST_HVAC_STATE = 0.0
                    ST_TEMP = device.temperature
                    ST_HUM = device.humidity
                    ST_TARGET = device.target

                if (device.name=='Basement (Shop)'):
                    if (str(device.hvac_state) == 'heating'):
                        BS_HVAC_STATE = 1.0
                    else:
                        BS_HVAC_STATE = 0.0

    except:
        print('Exception in Nest API call: '+str(sys.exc_info()[0])+' ['+str(datetime.datetime.now())+']' )
    else:
        print ("NEST api call complete: ["+str(datetime.datetime.now())+"]")

        US_HVAC_STATE = MB_HVAC_STATE + UP_HVAC_STATE + ST_HVAC_STATE

        if (US_HVAC_STATE != 0.0):
            US_HVAC_STATE = US_HVAC_STATE + 1.0


        if US_HVAC_STATE > 1.0:
            US_CORR = 1.0
        else:
            US_CORR = 0.0

        if DS_HVAC_STATE  < 1.0:
            DS_CORR = 0.0
        else:
            DS_CORR = 1.0

        EST_POWER = DS_CORR * DS_POWER + US_CORR * US_POWER + BS_HVAC_STATE * BS_POWER

        if LAST_DS != DS_CORR:
            if DS_CORR > 0.5:
                ds_period = time.time() - ds_rising_time
                if ds_period != 0.0:
                    ds_duty_cycle = ds_high_time/ds_period
                ds_rising_time = time.time()
            else:
                ds_high_time = time.time() - ds_rising_time
        statsdb.statsdb('DS_DUTY_CYCLE', ds_duty_cycle)
        statsdb.statsdb('DS_PERIOD', ds_period)
        LAST_DS = DS_CORR

        if LAST_US != US_CORR:
            if US_CORR > 0.5:
                us_period = time.time() - us_rising_time
                if us_period != 0.0:
                    us_duty_cycle = us_high_time/us_period
                us_rising_time = time.time()
            else:
                us_high_time = time.time() - us_rising_time
        statsdb.statsdb('US_DUTY_CYCLE', us_duty_cycle)
        statsdb.statsdb('US_PERIOD', us_period)
        LAST_US = US_CORR
            
        power_sample[iring] = EST_POWER #update ring buffer with power samples
        iring = iring + 1
        
        if iring >= RING_SIZE:
            iring = 0
        if jring < RING_SIZE-1:
            power_sample.append(0.0)

        AVG_EST_POWER = 0.0
        for i in range(0,jring):
            AVG_EST_POWER = AVG_EST_POWER + power_sample[i]
        AVG_EST_POWER = AVG_EST_POWER/float(jring+1)
        if jring+1 < RING_SIZE-1: # so that jring goes from 0 to RING_SIZE-1 then stays at RING_SIZE-1
            jring = jring + 1


        statsdb.statsdb('EST_POWER', EST_POWER)
        #print ("Est Power statsd was called with: " + str(EST_POWER))

        statsdb.statsdb('AVG_EST_POWER', AVG_EST_POWER)
        #print ("Avg Est Power statsd was called with: " + str(AVG_EST_POWER))

        statsdb.statsdb('DS_HVAC', DS_HVAC_STATE)
        #print ("Downstairs statsd was called with: " + str(DS_HVAC_STATE))

        statsdb.statsdb('DS_TARGET', DS_TARGET)
        #print ("Downstairs Target statsd was called with: " + str(DS_TARGET))

        statsdb.statsdb('DS_HUM', DS_HUM)
        #print ("Downstairs Humidity statsd was called with: " + str(DS_HUM))        
        
        statsdb.statsdb('ST_TARGET', ST_TARGET)
        #print ("Studio Target statsd was called with: " + str(ST_TARGET))

        statsdb.statsdb('US_HVAC', US_HVAC_STATE)
        #print ("Upstairs statsd was called with: " + str(US_HVAC_STATE))

        statsdb.statsdb('MB_HVAC', MB_HVAC_STATE)
        #print ("Master Bedroom statsd was called with: " + str(MB_HVAC_STATE))

        statsdb.statsdb('MB_HUM', MB_HUM)
        #print ("Master Bedroom Humidity statsd was called with: " + str(MB_HUM))
               
        statsdb.statsdb('UP_HVAC', UP_HVAC_STATE)
        #print ("Upstairs statsd was called with: " + str(UP_HVAC_STATE))

        statsdb.statsdb('BS_HVAC', BS_HVAC_STATE)
        #print ("Basement statsd was called with: " + str(BS_HVAC_STATE))

        statsdb.statsdb('ST_HVAC', ST_HVAC_STATE)
        #print ("Studio statsd was called with: " + str(ST_HVAC_STATE))

        statsdb.statsdb('ST_TEMP', ST_TEMP)
        #print ("Studio statsd called with temp: ", str(ST_TEMP))

        statsdb.statsdb('ST_HUM', ST_HUM)
        #print ("Studio statsd called with humidity: ", str(ST_HUM))

        statsdb.statsdb('ST_TARGET', ST_TARGET)
        #print ("Studio statsd called with target: ", str(ST_TARGET))        

        ST_DELTA = ST_TEMP - ST_TARGET
        statsdb.statsdb('ST_DELTA', ST_DELTA)
        #print ("Studio statsd called with delta: ", str(ST_DELTA))

    sys.stdout.flush()
    time.sleep(20)
pass

