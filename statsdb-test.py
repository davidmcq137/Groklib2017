from __future__ import print_function
from __future__ import with_statement

import xmltodict
import statsdb

chan_dict={'Garage_temp' : ['current_observation', 'davis_current_observation','temp_extra_1'],
           'Outside_temp': ['current_observation', 'temp_f'],
           'Humidity'    : ['current_observation', 'relative_humidity'],
           'Barometer'   : ['current_observation', 'pressure_in'],
           'Fazzone'     : ['current_observation', 'marshall'],
           'XYZ'         : ['fazzone', 'marshall'],
           'Garage_wzyx' : ['current_observation', 'davis_current_observation','temp_extra_Z'],
           'Garage_xyzw' : ['current_observation', 'xyzzy','temp_extra_1'] }
    
with open('~/weatherlink.xml', 'r') as fp:
    xml_body = fp.read()

curr_api_dict = xmltodict.parse(xml_body)

statsdb.write_channels(curr_api_dict, chan_dict, prt=True, sdb=False)
                
