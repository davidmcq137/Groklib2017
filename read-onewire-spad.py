#!/usr/bin/env python

from w1thermsensor import W1ThermSensor
from datadog import statsd
import time
import sys
import socket


# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening

server_address = ('10.0.0.48', 10137)

id_to_name = ["000008290883","Inside Temp"]

for sensor in W1ThermSensor.get_available_sensors():
    print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))

while True:

    sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, id_to_name[0])
    temp = sensor.get_temperature(W1ThermSensor.DEGREES_F)
    #statsd.gauge(id_to_name[1], temp)
    print("Called statsd with: " + id_to_name[1] + " " + str(temp))
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print >>sys.stderr, 'connecting to %s port %s' % server_address
        sock.connect(server_address)
	sockpayload = id_to_name[1] + "," + str(int(time.time())) + "," + str(temp) + ",DD" + ",spad"
	print sockpayload
        sock.sendall(sockpayload)
    except:
        print "Exception calling sock.sendall at [" + str(int(time.time())) + "]"
    finally:
        sock.close()

    print(" ")
    sys.stdout.flush()
    time.sleep(30)
pass


