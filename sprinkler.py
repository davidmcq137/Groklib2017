from __future__ import print_function

import sys,os
import time
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import piplates.RELAYplate as RELAY
import statsdb

def handle(progname):
    global wakeup
    #print('in handle')
    if progname == 'rain.data':
        print('Handling ', progname)
        wakeup = True

class Handler(FileSystemEventHandler):
    def on_modified(this, event):
        if event.is_directory:
            return None
        progname = event.src_path[2:]
        handle(progname)

def main():
    global wakeup
    ppADDR = 1
    rain_threshold = 1.0
    spr_state = 0.0

    observer = Observer()
    observer.schedule(Handler(), ".", recursive=False)
    observer.start()
    RELAY.RESET(ppADDR)

    while True:
        print('Iterating')
        if wakeup:
            try:
                pf = open('rain.data', 'r')
                print('Opened file rain.data')
                line = pf.readline()
                pf.close()
                sline = line.split(',')
                rv = float(sline[0])
                rtime = datetime.datetime.now()
                print('File rain.data timestamp: ', sline[1])
                print('Weighted rain amount -3/+3: ', sline[0])
                print('Rain threshold to enable sprinkler: ', rain_threshold)
                if rv > rain_threshold:
                    print('Sprinkler Disabled: Relay OFF at ', rtime)
                    RELAY.relayOFF(ppADDR, 1)
                    spr_state = 0.0
                else:
                    print('Sprinkler Enabled: Relay ON at ', rtime)
                    RELAY.relayON(ppADDR, 1)
                    spr_state = 1.0

            except (ValueError,EOFError):
                ierr = ierr + 1
            wakeup = False
        statsdb.statsdb('SprinklerEN', spr_state)
        time.sleep(100.0)



if __name__ == "__main__":

    wakeup = False
    main()
