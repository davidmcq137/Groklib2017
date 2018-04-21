from __future__ import print_function

# from sys import argv
import subprocess
import statsdb
import time

hazel_up = True

j=0
while True:
    j=j+1
    ispc = subprocess.call(["ping", "-c",  "3", "10.0.0.48"])
    if j == 3:
        ispc = 1
        
    print ("ispc: ", ispc)

    if ispc == 0 and hazel_up == False:
        hazel_up = True
        statsdb.send_sms_ltd ("Hazel came back up!", "dfm_cell")
        
    if ispc != 0 and hazel_up == True:
        hazel_up = False
        statsdb.send_sms_ltd ("Hazel went down!", "dfm_cell")

    time.sleep(10)
    
