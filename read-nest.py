import nest
import sys
from datadog import statsd
import time
import datetime
import ConfigParser
import os

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
while True:
    try:
        for structure in napi.structures:
            for device in structure.thermostats:
                print(device.name)
                if (device.name=='Downstairs'):
                     DS_TARGET = device.target
                     if (str(device.hvac_state) == 'heating'):
                         DS_HVAC_STATE = 1.0
                     else:
                        DS_HVAC_STATE = 0.1

# For Downstairs (one device), it's just 0 or 1
# For Upstairs (three devices), it's 0 or 1.1, 1.2, 1.3

                if (device.name=='Master Bedroom'):
                    if (str(device.hvac_state) == 'heating'):
                        MB_HVAC_STATE = 0.1
                    else:
                        MB_HVAC_STATE = 0.0
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

        statsd.gauge('DS_HVAC', DS_HVAC_STATE)
        print ("Downstairs statsd was called with: " + str(DS_HVAC_STATE))

        statsd.gauge('DS_TARGET', DS_TARGET)
        print ("Downstairs Target statsd was called with: " + str(DS_TARGET))

        statsd.gauge('US_HVAC', US_HVAC_STATE)
        print ("Upstairs statsd was called with: " + str(US_HVAC_STATE))


        statsd.gauge('MB_HVAC', MB_HVAC_STATE)
        print ("Master Bedroom statsd was called with: " + str(MB_HVAC_STATE))

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
        ST_DELTA = ST_TEMP - ST_TARGET
        statsd.gauge('ST_DELTA', ST_DELTA)
        print ("Studio statsd called with delta: ", str(ST_DELTA))

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
