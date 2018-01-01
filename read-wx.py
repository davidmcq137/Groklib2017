#!/usr/bin/env python

from __future__ import print_function

import re
import os
import time
import sys
import sqlite3
import datetime
from datadog import statsd

Wx_XML_File="/var/www/html/weewx/RSS/weewx_rss.xml"

Davis_WX_Outside_T  = 0.0
Davis_WX_Inside_T   = 0.0
Davis_WX_Humidity   = 0.0
Davis_WX_Barometer  = 0.0

with open('/tmp/read-wx.py.pid', 'w') as f:
    f.write(str(os.getpid()))

conn = sqlite3.connect('/var/lib/weewx/weewx.sdb')

while True:
    cur = conn.cursor()

    cur.execute('''select
    dateTime, barometer, inTemp, outTemp, extraTemp1, outHumidity, windSpeed, windDir
    from archive order by dateTime desc limit 1;''')

    _, bar, in_temp, out_temp, extra_temp, humidity, wind_speed, wind_dir = cur.fetchone()

    params = {
        "Outside Temp": out_temp,
        "Inside Temp": in_temp,
        "Humidity": humidity,
        "Barometer": bar,
        "Garage Temp": extra_temp,
        "Humidity": humidity,
        "Wind Direction": wind_dir,
        "Wind Speed": wind_speed}

    for name, value in params.iteritems():
        print(name, value)
        if value:
            statsd.gauge(name, value)

    sys.stdout.flush()
    time.sleep(100)


pass #end while

