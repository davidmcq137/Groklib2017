#!/usr/bin/env python
from __future__ import print_function
import socket
import time
import os
import platform

server_address = ('10.0.0.48',10137)

def statsdb(channel, value):
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        pyname = os.path.basename(__file__)
        sockpayload = (channel + "," + str(int(time.time())) + ","
                       + str(value) + ",DD" + "," + platform.node())
        # print("sockpayload: ", sockpayload)
        sock.sendall(sockpayload)
    except:
        print ("Exception calling sock.sendall at [" + str(int(time.time())) + "]")
    finally:
        sock.close()

    return



