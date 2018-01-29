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
    
    print(curr_api_dict['current_observation']['observation_time'])
    
    pressure_in = float(curr_api_dict['current_observation']['pressure_in'])
    print("pressure_in: ", curr_api_dict['current_observation']['pressure_in'])

    wind_mph = float(curr_api_dict['current_observation']['wind_mph'])
    print("wind_mph: ", curr_api_dict['current_observation']['wind_mph'])

    wind_degrees = float(curr_api_dict['current_observation']['wind_degrees'])
    print("wind_degrees: ", curr_api_dict['current_observation']['wind_degrees'])

    temp_f = float(curr_api_dict['current_observation']['temp_f'])
    print("temp_f: ", curr_api_dict['current_observation']['temp_f'])

    relative_humidity = curr_api_dict['current_observation']['relative_humidity']
    print("relative_humidity: ", relative_humidity)

    # lower_garage = curr_api_dict['current_observation']['davis_current_observation']['temp_extra_1']
    # print("Lower Garage Temp: ", lower_garage)


    print("Observation age: ",
          curr_api_dict['current_observation']['davis_current_observation']['observation_age'])

    statsdb.statsdb("Davis Outside Temp", temp_f)
    statsdb.statsdb("Davis Barometer", pressure_in)
    statsdb.statsdb("Davis Humidity", relative_humidity)
    statsdb.statsdb("Davis Wind Speed", wind_mph)
    statsdb.statsdb("Davis Wind Direction", wind_degrees)
    # statsdb.statsdb("Davis Garage Temp", lower_garage)

    sys.stdout.flush()
    time.sleep(120)
    
