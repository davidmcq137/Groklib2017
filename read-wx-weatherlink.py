#!/usr/bin/env python

from __future__ import print_function
import requests
import xmltodict
import ConfigParser
import os
import sys
import time
import datetime
import statsdb

config = ConfigParser.ConfigParser()
osp = os.path.expanduser('~/weatherlink.conf')
config.read(osp)

api_key    = config.get('KEYS', 'api_key')
DID        = config.get('KEYS', 'device_id')
device_key = config.get('KEYS', 'device_key')
device_pwd = config.get('KEYS', 'device_pwd')

print("api_key: ", api_key)
print("DID: ", DID)
print("device_key: ", device_key)
print("password: ", device_pwd)

# Current Conditions
# http://api.weatherlink.com/v1/NoaaExt.xml?user=DID&pass=password&apiToken=xxx

# Station Metadata
# http://api.weatherlink.com/v1/StationStatus.xml?user=DID&pass=password&apiToken=xxx
 
 
url_str_P = 'http://api.weatherlink.com/v1/NoaaExt.xml?user='
url_str = url_str_P + DID + "&pass=" + device_pwd + "&apiToken=" + api_key

#print("url_str: ", url_str)

with open('/tmp/read-wx-weatherlink.py.pid', 'w') as f:
    f.write(str(os.getpid()))
    
errs=0
last_epoch = 0
skip_curr =  8  # only read wx every 8x main sleep loop of 120s (2 min) = every 16  min

while True:

    if (skip_curr >= 8):

        skip_curr = 0

        print("Requesting current weather from Weatherlink at: ", datetime.datetime.now())

        try:
            rc = requests.get(url_str)
            with open('/tmp/weatherlink.text', 'w') as fw:
                fw.write(rc.text)
            #print(rc.text)
            curr_api_dict = xmltodict.parse(rc.text)
            errs=0
        except:
            print("Error reading current weather data from Davis Weatherlink")
            print(url_str)
            errs = errs + 1
            if errs > 20:
                print("Exiting due to persistent errors reading weather")
                sys.stdout.flush()
                exit()
                time.sleep(30)
                continue
    # end skip_curr
    
    skip_curr = skip_curr + 1

    print("skip_curr: ", skip_curr)
    
    print(datetime.datetime.now())
    
    print(curr_api_dict.get('current_observation').get('observation_time'))
    
    dd = curr_api_dict.get('current_observation').get('pressure_in')
    if dd == None:
          pressure_in = 'None'
    else:
          pressure_in = float(dd)
          
    print("pressure_in: ", pressure_in)

    dd = curr_api_dict.get('current_observation').get('wind_mph')
    if dd == None:
          wind_mph = 'None'
    else:
          wind_mph = float(dd)

    dd  = curr_api_dict.get('current_observation').get('wind_degrees')
    if dd == None:
          wind_degrees = 'None'
    else:
          wind_degrees = float(dd)

    dd = curr_api_dict.get('current_observation').get('temp_f')
    if dd == None:
        temp_f = 'None'
    else:
        temp_f = float(dd)
    

    dd  = curr_api_dict.get('current_observation').get('relative_humidity')
    if dd == None:
          relative_humidity = 'None'
    else:
          relative_humidity = float(dd)
          
    print("relative_humidity: ", relative_humidity)

    dd = curr_api_dict.get('current_observation').get('davis_current_observation').get('temp_extra_1')
    if dd == None:
          lower_garage = 'None'
    else:
          lower_garage = float(dd)
          
    print("Lower Garage Temp: ", lower_garage)


    print("Observation age: ",
          curr_api_dict.get('current_observation').get('davis_current_observation').get('observation_age'))


    sm1 = curr_api_dict.get('current_observation').get('davis_current_observation').get('soil_moisture_1')
    print("Soil Moisture 1: ", sm1)

    sm2 = curr_api_dict.get('current_observation').get('davis_current_observation').get('soil_moisture_2')
    print("Soil Moisture 2: ", sm2)

    ts1 = curr_api_dict.get('current_observation').get('davis_current_observation').get('temp_soil_1')
    print("Soil Temp 1: ", ts1)

    ts2 = curr_api_dict.get('current_observation').get('davis_current_observation').get('temp_soil_2')
    print("Soil Temp 2: ", ts2)

    statsdb.statsdb("Davis Outside Temp", temp_f)
    statsdb.statsdb("Davis Barometer", pressure_in)
    statsdb.statsdb("Davis Humidity", relative_humidity)
    statsdb.statsdb("Davis Wind Speed", wind_mph)
    statsdb.statsdb("Davis Wind Direction", wind_degrees)
    statsdb.statsdb("Davis Garage Temp", lower_garage)
    statsdb.statsdb("Davis Soil Moisture 1", sm1)
    statsdb.statsdb("Davis Soil Moisture 2", sm2)
    statsdb.statsdb("Davis Soil Temp 1", ts1)
    statsdb.statsdb("Davis Soil Temp 2", ts2)

    sys.stdout.flush()
    time.sleep(120)
    
