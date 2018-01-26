#!/usr/bin/env python

from __future__ import print_function
import requests
import json
import ConfigParser
import os
import sys
import time
import datetime
import statsdb

config = ConfigParser.ConfigParser()
osp = os.path.expanduser('~/weather_underground.conf')
config.read(osp)

user_api = config.get('KEYS', 'api_key')

url_str_P = 'http://api.wunderground.com/api/'
url_str_C = '/geolookup/conditions/q/NY/Yorktown_Heights.json'
url_str_F = '/forecast/q/NY/Yorktown_Heights.json'

#print("url_str: ", url_str)

with open('/tmp/read-wx-WU.py.pid', 'w') as f:
    f.write(str(os.getpid()))
    
errs=0
last_epoch = 0
skip_curr = 4   # only read wx every 4x main sleep loop of 120s (2 min) = every 8 min
skip_fcst = 40  # make sure on startup it reads on first time thru so variables are defined and stored

while True:

    if (skip_curr >= 4):

        skip_curr = 0

        print("Requesting current weather at: ", datetime.datetime.now())

        try:
            url_str = url_str_P + user_api + url_str_C
            rc = requests.get(url_str)
            curr_api_dict = rc.json()
            errs=0
        except:
            print("Error reading current weather data from Weather Underground")
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
    
    if (skip_fcst >= 40):

        skip_fcst = 0

        print("Requesting forecast weather at: ", datetime.datetime.now())

        try:
            url_str = url_str_P + user_api + url_str_F
            rf = requests.get(url_str)
            fcst_api_dict = rf.json()
            errs=0
        except:
            print("Error reading forecast data from Weather Underground")
            print(url_str)
            errs = errs + 1
            if errs > 20:
                print("Exiting due to persistent errors reading weather")
                sys.stdout.flush()
                exit()
                time.sleep(30)
                continue
    # end skip_fcst
    
    skip_fcst = skip_fcst + 1

    dstr = fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['date']['pretty']
    print ("Forecast date: ", dstr)
    
    fcst_high = float(fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit'])
    print ("Fcst Hi: ", fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit'])

    fcst_low = float(fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['low']['fahrenheit'])
    print ("Fcst Lo: ", fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['low']['fahrenheit'])

    pressure_in = float(curr_api_dict['current_observation']['pressure_in'])
    print("pressure_in: ", curr_api_dict['current_observation']['pressure_in'])

    wind_mph = float(curr_api_dict['current_observation']['wind_mph'])
    print("wind_mph: ", curr_api_dict['current_observation']['wind_mph'])

    wind_degrees = float(curr_api_dict['current_observation']['wind_degrees'])
    print("wind_degrees: ", curr_api_dict['current_observation']['wind_degrees'])

    temp_f = float(curr_api_dict['current_observation']['temp_f'])
    print("temp_f: ", curr_api_dict['current_observation']['temp_f'])

    rh_raw = curr_api_dict['current_observation']['relative_humidity']
    relative_humidity = float(rh_raw[:-1]) # remove the "%"
    print("relative_humidity: ", relative_humidity)

    obs_epoch = int(curr_api_dict['current_observation']['observation_epoch'])
    print("observation_epoch: ", obs_epoch)
    if obs_epoch != last_epoch: 
        print("Delta time from last reported epoch (m): ", (obs_epoch - last_epoch)/60.0)
    last_epoch = obs_epoch
    
    statsdb.statsdb("Outside Temp", temp_f)
    statsdb.statsdb("Barometer", pressure_in)
    statsdb.statsdb("Humidity", relative_humidity)
    statsdb.statsdb("Wind Speed", wind_mph)
    statsdb.statsdb("Wind Direction", wind_degrees)

    statsdb.statsdb("Forecast High", fcst_high)
    statsdb.statsdb("Forecast Low", fcst_low)
            
    
    sys.stdout.flush()
    time.sleep(120)
    
