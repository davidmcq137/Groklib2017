#!/usr/bin/env python
from __future__ import print_function
import datetime
import json
import requests
import ConfigParser
import os
import sys
import time
import statsdb


def time_converter(time):
    # print("time_converter input"+str(time))
    converted_time = datetime.datetime.utcfromtimestamp(
        int(time)
    ).strftime('%I:%M %p')
    return converted_time


def url_builder(city_id, user_api):

    unit = 'imperial'  # For Fahrenheit use imperial, for Celsius use metric, and the default is Kelvin.
    api = 'http://api.openweathermap.org/data/2.5/weather?id='
    # Search for your city ID here: http://bulk.openweathermap.org/sample/city.list.json.gz

    full_api_url = api + str(city_id) + '&mode=json&units=' + unit + '&APPID=' + user_api
    #print("Full URL:")
    #print(full_api_url)
    return full_api_url


#def data_fetch(full_api_url):
#    url = urllib.request.urlopen(full_api_url)
#    output = url.read().decode('utf-8')
#    raw_api_dict = json.loads(output)
#    url.close()
#    return raw_api_dict

def data_fetch(full_api_url):
    r = requests.get(full_api_url)
    raw_api_dict = r.json()
    return raw_api_dict



def data_organizer(raw_api_dict):

    #print ("Raw api dict")
    #print (raw_api_dict)
    #print ("End raw api dict")
    if raw_api_dict.get('rain') == None:
        r3h = 0
    else:
        r3h = raw_api_dict.get('rain').get('3h')

    #print ("rain3h: ", r3h)
    try:
        country=raw_api_dict.get('sys').get('country'),
    except:
        print("exception on country=raw...")
        print(raw_api_dict)
        return None
            
    data = dict(

        city=raw_api_dict.get('name'),
        country=raw_api_dict.get('sys').get('country'),
        temp=raw_api_dict.get('main').get('temp'),
        temp_max=raw_api_dict.get('main').get('temp_max'),
        temp_min=raw_api_dict.get('main').get('temp_min'),
        humidity=raw_api_dict.get('main').get('humidity'),
        pressure=raw_api_dict.get('main').get('pressure'),
        sky=raw_api_dict['weather'][0]['main'],
        sunrise=time_converter(raw_api_dict.get('sys').get('sunrise')),
        sunset=time_converter(raw_api_dict.get('sys').get('sunset')),
        wind=raw_api_dict.get('wind').get('speed'),
        wind_deg=raw_api_dict.get('wind').get('deg'),
        dt=time_converter(raw_api_dict.get('dt')),
        dtepoch=raw_api_dict.get('dt'),
        cloudiness=raw_api_dict.get('clouds').get('all'),
        rain3h=r3h

    )
    #print("data dict returned: ", data)
    
    return data


def data_output(data):
    m_symbol = '\xb0' + 'F'
    print('---------------------------------------')
    print('Current weather in: {}, {}:'.format(data['city'], data['country']))
    print(data['temp'], m_symbol, data['sky'])
    print('Max: {}, Min: {}'.format(data['temp_max'], data['temp_min']))
    print('')
    print('Wind Speed: {}, Degree: {}'.format(data['wind'], data['wind_deg']))
    print('Humidity: {}'.format(data['humidity']))
    print('Cloud: {}'.format(data['cloudiness']))
    inHg_pressure = data['pressure'] * 0.029530
    print('Rain 3H: {}'.format(data['rain3h']))
    print('Pressure: {:.2f}'.format(inHg_pressure))
    print('Sunrise at: {}'.format(data['sunrise'])+' UTC')
    print('Sunset at: {}'.format(data['sunset']) + ' UTC')
    print('')
    print('Last update from the server: {}'.format(data['dt'])+' UTC')
    print('---------------------------------------')

last_epoch = 0
    
config = ConfigParser.ConfigParser()
osp = os.path.expanduser('~/open_weather.conf')
config.read(osp)

user_api = config.get('KEYS', 'api_key')
KatonahNY = 5123118

print("Open Weather API key: ", user_api)

with open('/tmp/read-wx-open.py.pid', 'w') as f:
    f.write(str(os.getpid()))
    
while True:
    try:
       wxdict = data_organizer(data_fetch(url_builder(KatonahNY, user_api)))
    except IOError:
        print('Error getting weather data')

    # print("wxdict:")
    # print(wxdict)

    if wxdict == None:
        time.sleep(120)
        continue
    
    print("Weather readings at: ", datetime.datetime.now())
    print("Last server update at " + wxdict['dt'] + " UTC")
    print("dtepoch: ", wxdict['dtepoch'])

    epoch = wxdict['dtepoch']
    if epoch < last_epoch:
        print("Wacky backwards epoch!!!!!!!!!!!!!!!!")
    last_epoch = epoch
    
    print ("wxdict['temp']: ", wxdict['temp'])
    statsdb.statsdb("OW Outside Temp", wxdict['temp'])
            
    print ("wxdict['pressure']", wxdict['pressure'] * 0.029530)
    statsdb.statsdb("OW Barometer", wxdict['pressure'] * 0.029530)
            
    print ("wxdict['humidity']", wxdict['humidity'])
    statsdb.statsdb("OW Humidity", wxdict['humidity'])
            
    print ("wxdict['wind']", wxdict['wind'])
    statsdb.statsdb("OW Wind Speed", wxdict['wind'])

    print ("wxdict['wind_deg']", wxdict['wind_deg'])
    statsdb.statsdb("OW Wind Direction", wxdict['wind_deg'])
            
    sys.stdout.flush()
    time.sleep(120)
    
# end while True
