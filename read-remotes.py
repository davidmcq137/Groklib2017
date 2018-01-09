#!/usr/bin/env python

from __future__ import print_function

import os
import time
import sys
import sqlite3
import datetime
import socket
import select
import datadog
from pathlib import Path

Remote_List = {}
CONNECTION_LIST = []    # list of socket clients
RECV_BUFFER = 256 # Advisable to keep it as an exponent of 2
PORT = 10137
tn = "HAZEL_MASTER"
timeout = 40.0    # seconds before a reading, once heard from, is considered late

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
server_socket.bind(("0.0.0.0", PORT))
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
                c.execute(sstr)
                conn.commit()
                print ("Length of dlist: ", len(dlist))
                print (dlist)
                if len(dlist) >=4 and dlist[3] == 'DD':
                    print ('Would call statsd.gauge with: ', dlist[0], dlist[2])
                    statsd.gauge(dlist[0], dlist[2])
                
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
            Remote_List[chan] = 0 # just print it once, it will get reset above if it wakes up
        #else:
            #print("Time,Channel, time ok: ", time.time(), chan, chan_time)
            
    time.sleep(0.2)
                  
# end while True

server_socket.close()
conn.close()

