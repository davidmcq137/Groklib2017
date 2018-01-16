#!/usr/bin/env python

from __future__ import print_function
#

import requests
import ConfigParser
import os
import time
import sys
import sqlite3
import datetime
import socket
import select
import subprocess
from datadog import statsd
from pathlib import Path
from requests.auth import HTTPBasicAuth

def send_sms(body, dest):
    
    config=ConfigParser.ConfigParser()
    osp = os.path.expanduser('~/twilio.conf')
    
    config.read(osp)

    t_acct   = config.get('KEYS', 'twilio_acct')
    t_user   = config.get('KEYS', 'twilio_user')
    t_pass   = config.get('KEYS', 'twilio_pass')

    t_num    = config.get('PHONES' , 'twilio_num')
    dfm_cell = config.get('PHONES'   , 'dfm_cell')
    lrm_cell = config.get('PHONES'   , 'lrm_cell')

    timestamp = datetime.datetime.now()
    
    ret_req = requests.post( "https://api.twilio.com/2010-04-01/Accounts/" + 
                    t_acct + "/Messages.json", auth = HTTPBasicAuth(t_user, t_pass),
                    data = {'To':   dest,'From': t_num,'Body': "[" + str(timestamp) + "] " + body})

    print("Requests returns: ", ret_req)

    print("send_sms:[" + str(timestamp) + "] sent \"" + body + "\" to "+dest)

    return ret_req


Remote_List = {}
CONNECTION_LIST = []    # list of socket clients
RECV_BUFFER = 256 # Advisable to keep it as an exponent of 2
PORT = 10137
tn = "HAZEL_MASTER"
timeout = 180.0   # seconds before a reading, once heard from, is considered late
watch_processes={"weewxd":0, "read-remotes.py":0, "read-wx.py":0, "read-ted.py":0, "read-wx.py":0}
iproc = 0
NPROC = 100

sql_db_fname = tn + ".db"
print("SQL data file name is: ", sql_db_fname)

# why oh why do you have to do Path() to make this work? calling .is_file with sql_db_fname fails

myfile = Path(sql_db_fname)

print("myfile: ", myfile)
    
if myfile.is_file():
    db_exists = True
else:
    db_exists = False
    
# Open the  database

conn = sqlite3.connect(sql_db_fname)
c = conn.cursor()
    
# Create table if we had to create the database

if db_exists:
    print ("Database file " + sql_db_fname + " WAS found, not creating table")
else:
    print ("Database file " + sql_db_fname + " NOT found, creating table: ")
    c.execute('CREATE TABLE ' + tn + '(CHAN string, EPOCH integer, VALUE real)')
    c = conn.cursor() # has the cursor moved if creating the table? re-read it

         
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#print ("Server socket: ", server_socket)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", PORT)) # maybe this should be 10.0.0.0 to only listen to local network?
server_socket.listen(10)
 
# Add server socket to the list of readable connections
CONNECTION_LIST.append(server_socket)
 
print ("SQLite read socket and insert loop started on port " + str(PORT))
 
while True:
    # use non-blocking form of select.select with last parm = 0.0
    read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[],0.0)
    # presumably if nothing read, for loop won't happen
    for sock in read_sockets:
        #New connection
        if sock == server_socket:
            # Handle the case in which there is a new connection received through server_socket
            sockfd, addr = server_socket.accept()
            CONNECTION_LIST.append(sockfd)
            #print ("Client (%s, %s) connected" % addr)
            #print ("CONNECTION_LIST is: ", CONNECTION_LIST)
        else:
            # Data recieved from client, process it
            data = sock.recv(RECV_BUFFER)
            if data:
                sock.close()
                CONNECTION_LIST.remove(sock)
                # print "Data are: [",data,"]"
                dlist = data.split(",")
                #print ("Data list: ", dlist)
                sstr=("INSERT INTO " + tn +" VALUES (" + "'" + dlist[0] + "'" + ","
                                     + str(dlist[1]) +"," +str(dlist[2]) +")")
                print("SQL insert: ", sstr)
                if dlist[0][0] != '#': # special first char .. if "#" then no value (E.g. wind dir)
                    c.execute(sstr)
                    conn.commit()
                #print ("Length of dlist: ", len(dlist))
                #print (dlist)
                if len(dlist) >=4 and dlist[3] == 'DD':
                    #print ('Would call statsd.gauge with: ', dlist[0], dlist[2])
                    if dlist[0][0] !='#':  #special first character .. no value for channel .. don't send
                        statsd.gauge(dlist[0], dlist[2]) # this is the only place in the system calling statsd
                
                # correct the string to remove the leading "#" before checking timing
                if dlist[0][0] == '#':
                    tempstr=dlist[0]
                    dlist[0] = tempstr[1:] 
                Remote_List[dlist[0]] = time.time() + timeout #shazam! works if new or old :-)
                # print ('Remote_List is: ', Remote_List)
                # endif
            # end if data
        # end else server_socket            
    # end for sock
    
    # now go thru arrival times list and see if someone is late
    for chan, chan_time in Remote_List.iteritems():
        if chan_time != 0 and time.time() > chan_time:
            print("Channel: " + chan + " is late!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            ret_sms = send_sms("Missing data from Channel: "+ chan, "+1-301-395-6242") 
            Remote_List[chan] = 0 # just print it once, it will get reset above if it wakes up
        #else:
            #print("Time,Channel, time ok: ", time.time(), chan, chan_time)

    # now look at the list of critical processes and see if they are still up and running

    iproc = iproc + 1
    if iproc >= NPROC: # main loop is 0.2 sec sleep, only check this every 20 secs if NPROC = 100
        iproc = 0
        ps_out = subprocess.check_output(["ps", "aux"])
        for process, ipc in watch_processes.iteritems():
            #print("Checking: ", process)
            if (not process in ps_out) and (ipc != -1):
                print("Process has stopped: ", process)
                # put sms call here
                body_str = "Process " + process + " has stopped."
                ret_sms = send_sms(body_str, "+1-301-395-6242")
                watch_processes[process]=-1
                # only want to send this message once, will reset if process restarts
            else:
                if (process in ps_out) and (ipc == -1):
                    print("Process has restarted: ", process)
                    # maybe sms call here?
                    body_str = "Process " + process + " has restarted."
                    ret_sms = send_sms(body_str, "+1-301-395-6242")
                    watch_processes[process]=1
                    #process is running, note it
    #end if iproc           
            
    time.sleep(0.2)
                  
# end while True

server_socket.close()
conn.close()

