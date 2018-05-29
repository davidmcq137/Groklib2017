from __future__ import print_function

# from sys import argv
import subprocess
import statsdb
import time

hazel_up = True


while True:

    ispc = subprocess.call(["ping", "-c",  "3", "10.0.0.48"])
        
    print ("ping return code: ", ispc)

    if ispc == 0 and hazel_up == False:
        hazel_up = True
        statsdb.send_sms_ltd ("Hazel not responding to ping", "dfm_cell")
        
    if ispc != 0 and hazel_up == True:
        hazel_up = False
        statsdb.send_sms_ltd ("Hazel resumed responding to ping", "dfm_cell")

    time.sleep(60)
    
