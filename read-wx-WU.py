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

url_str_H1 = '/history_'
url_str_H2 = '/q/NY/Yorktown_Heights.json'


#print("url_str: ", url_str)

with open('/tmp/read-wx-WU.py.pid', 'w') as f:
    f.write(str(os.getpid()))
    
errs=0
last_epoch = 0
SKPCMAX=4
skip_curr = SKPCMAX   # only read wx every 4x main sleep loop of 120s (2 min) = every 8 min
skip_fcst = 40        # make sure on startup it reads on first time thru so variables are defined and stored
day_of_year = time.localtime().tm_yday
old_day = 0 # make sure it runs first time thru at startup

while True:

    if (skip_curr >= SKPCMAX):

        skip_curr = 0

        print("Requesting current weather at: ", datetime.datetime.now())

        try:
            cur_url_str = url_str_P + user_api + url_str_C
            cur_rc = requests.get(cur_url_str)
            curr_api_dict = cur_rc.json()
            errs=0
        except:
            print("Error reading current weather data from Weather Underground")
            print(cur_url_str)
            print(cur_rc)
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

    skipstat = False
    
    if 'forecast' in fcst_api_dict:
        dstr = fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['date']['pretty']
        #print ("Forecast date: ", dstr)
    
        fcst_high = float(fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit'])
        #print ("Fcst Hi: ", fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit'])

        fcst_low = float(fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['low']['fahrenheit'])
        #print ("Fcst Lo: ", fcst_api_dict['forecast']['simpleforecast']['forecastday'][0]['low']['fahrenheit'])

        qpf3 = 0.0
        for q in range(4):
            tmp  = fcst_api_dict['forecast']['simpleforecast']['forecastday'][q]['qpf_allday']['in']
            if tmp != None:
                qpf3 = qpf3 + fcst_api_dict['forecast']['simpleforecast']['forecastday'][q]['qpf_allday']['in']
            
        print ('Rain3d: ', qpf3)

    else:
        print("<forecast> key not in response from WU")
        #print(fcst_api_dict)
        skipstat = True
        
    if 'current_observation' in curr_api_dict:
        pressure_in = float(curr_api_dict['current_observation']['pressure_in'])
        #print("pressure_in: ", curr_api_dict['current_observation']['pressure_in'])

        wind_mph = float(curr_api_dict['current_observation']['wind_mph'])
        #print("wind_mph: ", curr_api_dict['current_observation']['wind_mph'])
        
        wind_degrees = float(curr_api_dict['current_observation']['wind_degrees'])
        #print("wind_degrees: ", curr_api_dict['current_observation']['wind_degrees'])

        temp_f = float(curr_api_dict['current_observation']['temp_f'])
        #print("temp_f: ", curr_api_dict['current_observation']['temp_f'])

        rh_raw = curr_api_dict['current_observation']['relative_humidity']
        relative_humidity = float(rh_raw[:-1]) # remove the "%"
        #print("relative_humidity: ", relative_humidity)

        obs_epoch = int(curr_api_dict['current_observation']['observation_epoch'])
        #print("observation_epoch: ", obs_epoch)
        if obs_epoch != last_epoch: 
            print("Delta time from last reported epoch (m): ", (obs_epoch - last_epoch)/60.0)
            last_epoch = obs_epoch
    else:
        print("<current_observation> key not in response from WU")
        print(cur_url_str)
        print(cur_rc)
        #print(curr_api_dict)
        skip_curr = SKPCMAX # read again next iteration
        skipstat = True
        
    if not skipstat:
        statsdb.statsdb("Outside Temp", temp_f)
        statsdb.statsdb("Barometer", pressure_in)
        statsdb.statsdb("Humidity", relative_humidity)
        statsdb.statsdb("Wind Speed", wind_mph)
        statsdb.statsdb("Wind Direction", wind_degrees)
        
        statsdb.statsdb("Forecast High", fcst_high)
        statsdb.statsdb("Forecast Low", fcst_low)
        statsdb.statsdb("Rain3d", qpf3)
        if old_day != 0:
            statsdb.statsdb("HistRain3d", precipi_f_3d_tot)
        
# is it a new day? if past midnite then day_of_year will not match old_day
# get last 3 days of history on rain in inches
# which is in WU history report as 'history' 'dailysummary' [0] 'precipi'
# sum it up and put in the channel HistRain3d

    day_of_year = time.localtime().tm_yday
    if day_of_year != old_day:
        old_day = day_of_year
        print("New day, getting WU history at ", datetime.datetime.now())

        now = datetime.datetime.now()
        precipi_f_3d_tot = 0.0
        for i in range(3):
            dt = datetime.timedelta(days=i-3)
            dc = now + dt
            dstr = dc.strftime('%Y%m%d')
            cur_url_str = url_str_P + user_api + url_str_H1 + dstr + url_str_H2
            print("Requesting weather history for " + dstr + " at: ", datetime.datetime.now())

            try:
                cur_rc = requests.get(cur_url_str)
                curr_api_dict = cur_rc.json()
                errs=0
            except:
                print("Error reading weather history data from Weather Underground")
                print(cur_url_str)
                print(cur_rc)
                errs = errs + 1
                if errs > 20:
                    print("Exiting due to persistent errors reading weather history")
                    sys.stdout.flush()
                    exit()
            if 'history' in curr_api_dict:       
                precipi = statsdb.read_nested_dict(curr_api_dict, ['history', 'dailysummary', 0, 'precipi'])
            else:
                precipi = 'None'
                print('<history> key not in response from WU')
            if precipi != 'None':
                precipi_f_3d_tot = precipi_f_3d_tot + float(precipi)
                print('precipi is: ', precipi)
            time.sleep(30) # don't hammer WU too many times in a minute
            
        print('precipi_f_3d_tot is: ', precipi_f_3d_tot)
        body = 'Weather Precip update - 3 Day Future Precip: ' + str(qpf3) + ' in.'
        statsdb.send_sms_ltd(body, 'dfm_cell')

    sys.stdout.flush()
    time.sleep(120)
    
