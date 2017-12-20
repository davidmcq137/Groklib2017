import nest
import sys
from datadog import statsd
import ConfigParser

config=ConfigParser.ConfigParser()
foo=config.read('home/pi/nest-test.conf')


print("Foo is: ", foo)

print config.get('KEYS', 'client_id')
print config.get('KEYS', 'client_secret')

#these keys were exposed and replaced

client_id = 'ee1d8567-1b58-4e07-a393-fae8a0aa4a28'
client_secret = 'ActeHqIx07OJY7T9Wwc3wjZTI'
access_token_cache_file = 'nest.json'

napi = nest.Nest(client_id=client_id, client_secret=client_secret, access_token_cache_file=access_token_cache_file)

if napi.authorization_required:
    print('Go to ' + napi.authorize_url + ' to authorize, then enter PIN below')
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
for structure in napi.structures:
    print ('Structure   : %s' % structure.name)
    print (' Postal Code                    : %s' % structure.postal_code)
    print (' Country                        : %s' % structure.country_code)
    print (' num_thermostats                : %s' % structure.num_thermostats)

# Access advanced device properties:
    for device in structure.thermostats:

        print ('        Device: %s' % device.name)
        print ('        Where: %s' % device.where)
        print ('            Mode       : %s' % device.mode)
        print ('            HVAC State : %s' % device.hvac_state)
        print ('            Fan        : %s' % device.fan)
        print ('            Fan Timer  : %i' % device.fan_timer)
        print ('            Temp       : %0.1fC' % device.temperature)
        print ('            Humidity   : %0.1f%%' % device.humidity)
        print ('            Target     : %0.1fC' % device.target)
        print ('            Eco High   : %0.1fC' % device.eco_temperature.high)
        print ('            Eco Low    : %0.1fC' % device.eco_temperature.low)
#       print ('            Amb Temp   : %0.1fC' % device.ambient_temperature_f)

        print ('            hvac_emer_heat_state  : %s' % device.is_using_emergency_heat)

        print ('            online                : %s' % device.online)

        if (device.name=='Downstairs'):
            if (device.hvac_state == 'on'):
                DS_HVAC_STATE = 1.0
            else:
                DS_HVAC_STATE = 0.0

            statsd.histogram('DS_HVAC', DS_HVAC_STATE)
            print ("statsd was called with: " + str(DS_HVAC_STATE))


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
