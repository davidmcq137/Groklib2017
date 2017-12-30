import re
import time
import sys
import datetime
from datadog import statsd

Wx_XML_File="/var/www/html/weewx/RSS/weewx_rss.xml"

Davis_WX_Outside_T  = 0.0
Davis_WX_Inside_T   = 0.0
Davis_WX_Humidity   = 0.0
Davis_WX_Barometer  = 0.0

while True:

# Add a Try/Except block here to protect file operations? Or just let it crash?

    f=open(Wx_XML_File, 'r')
    myfile=f.read()
    f.close()

    result = re.search("<p>(.*?)</p>", myfile, re.DOTALL)

    if result:
        current_block_result=result.group(1)
    else:
        current_block_result='Not Found current_block__result'

    lines=current_block_result.splitlines()

# in case of N/A causing error on float, let it "flatline" at prior value

    try:
        Davis_WX_Outside_T  = float(lines[2][34:38])
    except:
        pass
    try:
        Davis_WX_Inside_T   = float(lines[3][34:38])
    except:
        pass
    try:
        Davis_WX_Humidity   = float(lines[7][34:36])
    except:
        pass
    try:
        Davis_WX_Barometer  = float(lines[8][34:40])
    except:
        pass

    print(datetime.datetime.now())
    print("Outside T: ", Davis_WX_Outside_T)
    print("Inside T: ", Davis_WX_Inside_T)
    print("Humidity: ", Davis_WX_Humidity)
    print("Barometer: ", Davis_WX_Barometer)

    statsd.gauge("Outside Temp", Davis_WX_Outside_T)
    statsd.gauge("Inside Temp", Davis_WX_Inside_T)
    statsd.gauge("Humidity", Davis_WX_Humidity)
    statsd.gauge("Barometer", Davis_WX_Barometer)

    time.sleep(300)

pass #end while


