#!/usr/bin/env python
from __future__ import print_function
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
import cPickle as pickle
from datadog import statsd
from pathlib import Path
from requests.auth import HTTPBasicAuth
from ISStreamer.Streamer import Streamer

timeout = 600.0         # seconds before a reading, once heard from, is considered late for channels and systems
iftime = time.time() + timeout
                        # post a time check <timeout> secs in the future to see if remote
                        # systems are up
Remote_Sys_List = {"Hazel":iftime, "thunderbolt":iftime, "camel":iftime, "spad":iftime, "jenny":iftime}

Remote_Chan_List = {}   # list of channels we are receiving
Remote_Chan_Vals = {}   # values of the channels
Remote_Chan_Sys =  {}   # system name the channel came from

CONNECTION_LIST = []    # list of socket clients
RECV_BUFFER = 16384     # advisable to keep it as an exponent of 2
PORT = 10137
tn = "HAZEL_MASTER"     # name stem for SQL logging database

#watch_processes={"weewxd":0,

watch_processes={"read-wx-WU.py":0,
                 "read-wx-weatherlink.py":0,
                 "read-wx-open.py":0,
                 "read-ted.py":0,
                 "read-nest.py":0,
                 "watch-read.py":0}  # watch-read.py watches this program (read-remotes)
iproc = 0
NPROC = 100
kproc = 0
HB_PROC = 1000

# read the config here so we have dfm_cell in the main prog
# inelegant that subroutine send_sms re-reads. think of a better way...

config=ConfigParser.ConfigParser()
osp = os.path.expanduser('~/twilio.conf')
config.read(osp)

dfm_cell = config.get('PHONES','dfm_cell')

print("Will text alerts to: ", dfm_cell)

config2=ConfigParser.ConfigParser()
osp = os.path.expanduser('~/InitialState.conf')
config2.read(osp)

accessKey = config2.get('KEYS','accessKey')
bucketKey = config2.get('KEYS','bucketKey')

print("Initial State Access key: ", accessKey)
print("Initial State Bucket key: ", bucketKey)

##### streamer = Streamer(bucket_name='Hazel', bucket_key=bucketKey, access_key=accessKey)
##### streamer.log("Log Messages", "read-remotes.py starting up at: " + str(datetime.datetime.now()))


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
    print("About to send_sms:[" + str(timestamp) + "] sent \"" + body + "\" to "+dest)
    
    try:
        ret_req = requests.post( "https://api.twilio.com/2010-04-01/Accounts/" + 
                    t_acct + "/Messages.json", auth = HTTPBasicAuth(t_user, t_pass),
                    data = {'To':   dest,'From': t_num,'Body': "[" + str(timestamp) + "] " + body},
                    timeout=2.0)
    except requests.exceptions.ConnectionError :
        print('ConnectionError exception in Twilio API call: ' + str(sys.exc_info()[0]) +
              ' ['+str(datetime.datetime.now())+']' )
        ret_req = -1
        
    #print("Requests returns: ", ret_req)

    return ret_req


sql_db_fname = tn + ".db"
print("SQL data file name is: ", sql_db_fname)

# why oh why do you have to do Path() to make this work? calling .is_file with sql_db_fname fails

myfile = Path(sql_db_fname)

#print("myfile: ", myfile)
    
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

for proc in watch_processes:
    print ("Watching process: ", proc)
         
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#print ("Server socket: ", server_socket)

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", PORT)) # maybe this should be 10.0.0.0 to only listen to local network?

# set max # backlog connection requests to 32, was 10 but some progs (e.g. read-nest.py) have more than
# 10 calls to statsdb .. and it was causing issues with late processing of channels
# just set it larger for now .. think about a more elegant solution
# e.g. making a subroutine to do batches of writes and sleeping every so many calls?
# checked /proc/sys/net/core/somaxconn for this system and max is 128

server_socket.listen(64)
 
# Add server socket to the list of readable connections
CONNECTION_LIST.append(server_socket)
 
print ("SQLite read socket and insert loop started on port " + str(PORT))

loop_time = 0.0
last_time = 0.0

while True:
    loop_time = time.time()
    if loop_time - last_time > 1.0 and last_time != 0:
        print("Loop time > 1 sec at " + str(datetime.datetime.now()) + ": ", str(loop_time-last_time))
        last_time = loop_time
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
                #print ("Data are: [",data,"]")
                dlist = data.split(",")
                #print ("Data list: ", dlist)
                time_loc = int(time.time())
                time_rem = int(dlist[1])
                if time_loc - time_rem > 10:
                    print("Time diff greater than 10s at: ", datetime.datetime.now())
                    print("Channel, loc time, rem time, delta: " + dlist[0] + " " + str(time_loc) +
                          " " + str(time_rem) + " " + str(time_loc-time_rem))
                # we are using the remote system's time .. should we use this system's time?    
                sstr=("INSERT INTO " + tn +" VALUES (" + "'" + dlist[0] + "'" + ","
                                     + str(dlist[1]) +"," +str(dlist[2]) +")")
                # special first char .. if "#" then no value (E.g. wind dir)
                # or in some cases "None" as a channel value from Wx readers
                if dlist[0][0] != '#' and dlist[2] != 'None':
                    #print("SQL insert: ", sstr)
                    t0 = time.time()
                    try:
                        c.execute(sstr)
                        conn.commit()
                    except:
                        print("Error on SQLite c.execute/conn.commit")
                        print("dlist: ", dlist)
                        print("sstr: ", sstr)
                    t1 = time.time()
                    if (t1-t0 > 100.0):
                        print("SQLite call longer than 100s at", datetime.datetime.now())
                #print ("Length of dlist: ", len(dlist))
                #print (dlist)
                if len(dlist) >=4 and dlist[3] == 'DD':
                    if dlist[0][0] !='#':  #special first character .. no value for channel .. don't send
                        #print ('Calling statsd.gauge with: ', dlist[0], dlist[2])
                        statsd.gauge(dlist[0], dlist[2]) # this is the only place in the
                                                         # system calling statsd exc heartbeat below
                        ##########streamer.log(dlist[0], dlist[2])
                        pass
                # correct the string to remove the leading "#" before checking timing
                if dlist[0][0] == '#':
                    tempstr=dlist[0]
                    dlist[0] = tempstr[1:]
                if dlist[0] in Remote_Chan_List:      # if a channel we know about
                  if Remote_Chan_List[dlist[0]] == 0: # if it got set to zero by being late then it's back
                      print("Channel has resumed reporting: ", dlist[0])
                lrlb = len(Remote_Chan_List)    
                Remote_Chan_List[dlist[0]] = time.time() + timeout #shazam! works if new or old :-)
                Remote_Chan_Vals[dlist[0]] = dlist[2]
                Remote_Chan_Sys [dlist[0]] = dlist[4]
                lrla = len(Remote_Chan_List)
                if lrla != lrlb:
                    print("Now tracking channel: ", dlist[0])
                # print ('Remote_Chan_List is: ', Remote_Chan_List)
                # endif
                if len(dlist) >= 5:     # if there is a system name in the message
                    if (dlist[4] in Remote_Sys_List):
                        if Remote_Sys_List[dlist[4]] == 0: # if it got set to zero by being late
                            print("Remote system is back up: ", dlist[4])
                        Remote_Sys_List[dlist[4]] = time.time() + timeout
                    else:
                        print("Unknown remote system: ", dlist[4])

                # end if len(ldlist)
            # end if data
        # end else server_socket            
    # end for sock
    
    # now go thru arrival times lists for channels and systems and see if someone is late

    latechan = False
    for chan, chan_time in Remote_Chan_List.iteritems():
        if chan_time != 0 and time.time() > chan_time:
            print("Missing data from channel: " + chan + " - sending text")
            ret_sms = send_sms("Missing data from Channel: "+ chan, dfm_cell) 
            Remote_Chan_List[chan] = 0 # just print it once, it will get reset above if it wakes up
            latechan = True # remember if a channel is late, no need to also print its system
            
    for sys_name, sys_time in Remote_Sys_List.iteritems():
        if sys_time != 0 and time.time() > sys_time:
            print("Missing data from system: " + sys_name)
            if not latechan:
                ret_sms = send_sms("Missing data from System: " + sys_name, dfm_cell) 
            Remote_Sys_List[sys_name] = 0 # just print it once, it will get reset above if it wakes up

    # send heartbeat signal to DD to be able to warn if this prog dies .. every 200 secs if HB_PROC=1000
    
    kproc = kproc + 1
    if kproc >= HB_PROC:
        kproc = 0
        statsd.gauge("HEART_BEAT", 137.137) # give a signal for DD to warn if this proc stops

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
                ret_sms = send_sms(body_str, dfm_cell)
                watch_processes[process]=-1
                # only want to send this message once, will reset if process restarts
            else:
                if (process in ps_out) and (ipc == -1):
                    print("Process has restarted: ", process)
                    # put sms call here?
                    body_str = "Process " + process + " has restarted."
                    ret_sms = send_sms(body_str, dfm_cell)
                    watch_processes[process]=1
                    #process is running, note it
        fpp = open('read-remotes.pkl', 'wb')
        pickle.dump(Remote_Sys_List, fpp)
        pickle.dump(Remote_Chan_List, fpp)
        pickle.dump(Remote_Chan_Vals, fpp)
        pickle.dump(Remote_Chan_Sys, fpp)
        pickle.dump(watch_processes, fpp)
        fpp.close()
    #end if iproc           
    sys.stdout.flush()
    time.sleep(0.2)
                  
# end while True

server_socket.close()
conn.close()

