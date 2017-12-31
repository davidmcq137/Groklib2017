#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import time
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

class Handler(FileSystemEventHandler):
    def on_modified(this, event):
        if event.is_directory:
            return None
        progname = event.src_path[2:]
        if not progname in watched_files:
            return None

        with open("/tmp/" + progname + ".pid") as pidfile:
            pid = int(pidfile.read())
            if is_running(pid):
                os.kill(pid, 3) # SIGQUIT
            start(progname)

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(Handler(), ".", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


    
