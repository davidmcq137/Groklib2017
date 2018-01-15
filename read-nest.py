#!/usr/bin/env python
from __future__ import print_function

import nest
import sys
from datadog import statsd
import time
import datetime
import ConfigParser
import os

DS_POWER = 5970.0
US_POWER = 6550.0
BS_POWER = 10800.0
AVG_EST_POWER = 0.0

with open('/tmp/read-nest.py.pid', 'w') as f:
    f.write(str(os.getpid()))

# set up a ring buffer for power samples. this prog's main loop is 20 seconds, so 3/min, 180/hr

# TODO: recode this so it starts 1 element, then adds one on each sample in each loop, only averages
# the number of samples it has so far, and wraps at 1000. This way is brain dead...

RING_SIZE = 1080                     # 6 hours
FILL_RING = 9400.0                   # make up a value close to what it should be
power_sample = [FILL_RING]           # declare list, set 0th element
for i in range(1,RING_SIZE):         # 1 thru RING_SIZE-1 for RING_SIZE elements
  power_sample.append(FILL_RING)

config=ConfigParser.ConfigParser()
osp = os.path.expanduser('~/read-nest.conf')

config.read(osp)

client_id = config.get('KEYS', 'client_id')
client_secret = config.get('KEYS', 'client_secret')

print(client_id)
print(client_secret)

access_token_cache_file = os.path.expanduser('~/nest.json')

print('Nest Monitor starting up:['+str(datetime.datetime.now())+']')

napi = nest.Nest(client_id=client_id, client_secret=client_secret, access_token_cache_file=access_token_cache_file)

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
    print ('Structure %s' % structure.name)
    print ('    Away: %s' % structure.away)
    print ('    Devices:')

    for device in structure.thermostats:
        print ('        Device: %s' % device.name)
        print ('            Temp: %0.1f' % device.temperature)

# Access advanced structure properties:

iring = 0 # average power ring buffer index

while True:
    try:
        for structure in napi.structures:
            for device in structure.thermostats:
                print(device.name)
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
        print ("Time: ["+str(datetime.datetime.now())+"]")

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

        power_sample[iring] = EST_POWER #update ring buffer with power samples
        iring = iring + 1
        if iring >= RING_SIZE:
            iring = 0


        AVG_EST_POWER = 0.0
        for i in range(0,RING_SIZE):
            AVG_EST_POWER = AVG_EST_POWER + power_sample[i]
        AVG_EST_POWER = AVG_EST_POWER/float(RING_SIZE)

        statsd.gauge('EST_POWER', EST_POWER)
        print ("Est Power statsd was called with: " + str(EST_POWER))

        statsd.gauge('AVG_EST_POWER', AVG_EST_POWER)
        print ("Avg Est Power statsd was called with: " + str(AVG_EST_POWER))

        statsd.gauge('DS_HVAC', DS_HVAC_STATE)
        print ("Downstairs statsd was called with: " + str(DS_HVAC_STATE))

        statsd.gauge('DS_TARGET', DS_TARGET)
        print ("Downstairs Target statsd was called with: " + str(DS_TARGET))

        statsd.gauge('DS_HUM', DS_HUM)
        print ("Downstairs Humidity statsd was called with: " + str(DS_HUM))        
        
        statsd.gauge('ST_TARGET', ST_TARGET)
        print ("Studio Target statsd was called with: " + str(ST_TARGET))

        statsd.gauge('US_HVAC', US_HVAC_STATE)
        print ("Upstairs statsd was called with: " + str(US_HVAC_STATE))

        statsd.gauge('MB_HVAC', MB_HVAC_STATE)
        print ("Master Bedroom statsd was called with: " + str(MB_HVAC_STATE))

        statsd.gauge('MB_HUM', MB_HUM)
        print ("Master Bedroom Humidity statsd was called with: " + str(MB_HUM))
               
        statsd.gauge('UP_HVAC', UP_HVAC_STATE)
        print ("Upstairs statsd was called with: " + str(UP_HVAC_STATE))

        statsd.gauge('BS_HVAC', BS_HVAC_STATE)
        print ("Basement statsd was called with: " + str(BS_HVAC_STATE))


        statsd.gauge('ST_HVAC', ST_HVAC_STATE)
        print ("Studio statsd was called with: " + str(ST_HVAC_STATE))

        statsd.gauge('ST_TEMP', ST_TEMP)
        print ("Studio statsd called with temp: ", str(ST_TEMP))

        statsd.gauge('ST_HUM', ST_HUM)
        print ("Studio statsd called with humidity: ", str(ST_HUM))

        statsd.gauge('ST_TARGET', ST_TARGET)
        print ("Studio statsd called with target: ", str(ST_TARGET))        

        ST_DELTA = ST_TEMP - ST_TARGET
        statsd.gauge('ST_DELTA', ST_DELTA)
        print ("Studio statsd called with delta: ", str(ST_DELTA))

    sys.stdout.flush()
    time.sleep(20)
pass


# The Nest object can also be used as a context manager
#with nest.Nest(client_id=client_id, client_secret=client_secret, access_token_cache_file=access_token_cache_file) as napi:
#    for device in napi.thermostats:
#        device.temperature = 23

# Nest products can be updated to include other permissions. Before you
# can access them with the API, a user has to authorize again. To handle this
# and detect when re-authorization is required, pass in a product_version
#client_id = 'XXXXXXXXXXXXXXX'
#client_secret = 'XXXXXXXXXXXXXXX'
#access_token_cache_file = 'nest.json'
#product_version = 1337

#napi = nest.Nest(client_id=client_id, client_secret=client_secret, access_token_cache_file=access_token_cache_file, product_version=product_version)

#print("Never Authorized: %s" % napi.never_authorized)
#print("Invalid Token: %s" % napi.invalid_access_token)
#print("Client Version out of date: %s" % napi.client_version_out_of_date)
#if napi.authorization_required is None:
#    print('Go to ' + napi.authorize_url + ' to authorize, then enter PIN below')
#    pin = input("PIN: ")
#    napi.request_token(pin)


# NOTE: By default all datetime objects are timezone unaware (UTC)
#       By passing `local_time=True` to the `Nest` object datetime objects
#       will be converted to the timezone reported by nest. If the `pytz`
#       module is installed those timezone objects are used, else one is
#       synthesized from the nest data
#napi = nest.Nest(username, password, local_time=True)
#print napi.structures[0].weather.current.datetime.tzinfo
