#!/usr/bin/env python
from __future__ import print_function
from __future__ import with_statement
import os
import sys
import time
import signal
import logging
import datetime
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

watched_files = {"read-ted.py": True,
                 "read-wx.py": True,
                 "read-nest.py": True}

def is_running(pid):        
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def logfilename(progname):
    return progname+".log"

def start(progname):
    logfile = open(logfilename(progname), "a")
    logfile.write("!!!!!!! Restarted " + progname + " at " + str(datetime.datetime.now()) + "\n")
    logfile.flush()
    command = "nohup pipenv run ./" + progname + " 2>/dev/null >> "+logfilename(progname)+" &"
    retval = os.system(command)
    if retval != 0:
        raise Exception("non-zero exit(" + str(revtal) + ": " + command)

def handle(progname):
    try:
        pidfile = open("/tmp/" + progname + ".pid") 
    except IOError:
        print("starting " + progname + " for the first time")
        start(progname)
    else:
        with pidfile:
            pid = int(pidfile.read())
            try:
                kr = os.kill(pid, signal.SIGKILL)
            except:
                print(progname + " not running?")
            else:
                print("killed " + progname + " (pid " + str(pid) + " + ret = " + str(kr) + ")")
            start(progname)
    
class Handler(FileSystemEventHandler):
    def on_modified(this, event):
        if event.is_directory:
            return None
        progname = event.src_path[2:]
        if not progname in watched_files:
            return None
        handle(progname)

if __name__ == "__main__":
    for name, _ in watched_files.iteritems():
        handle(name)
        
    observer = Observer()
    observer.schedule(Handler(), ".", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


    
