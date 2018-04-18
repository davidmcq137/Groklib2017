#!/usr/bin/env python

# expects to be run from virtualenv

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

watched_files = {"read-ted.py"             : True,
                 "read-wx-weatherlink.py"  : True,
                 "read-wx-WU.py"           : True,
                 "read-wx-open.py"         : True,
                 "read-nest.py"            : True,
                 "watch-read.py"           : True,
                 "read-remotes.py"         : True}

watched_short = {"read-ted.py"             : "RT" ,
                 "read-wx-weatherlink.py"  : "RWW",
                 "read-wx-WU.py"           : "RWU",
                 "read-wx-open.py"         : "RWO",
                 "read-nest.py"            : "RN" ,
                 "watch-read.py"           : "WR" ,
                 "read-remotes.py"         : "RR" }

def is_running(pid):        
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def logfilename(progname):
    return progname + ".log"

def start(progname):
    print('Starting ', progname)

    command = 'tmux new -d -s ' + '"' + watched_short[progname] \
              + '"' + ' "pipenv run python ' + progname + '"'
    print("tmux new command: ", command)

    retval = os.system(command)
    if retval != 0:
        raise Exception("tmux new: non-zero exit: " + str(retval) + ": " + command)

    ld = datetime.datetime.now()
    log_date_str = ld.strftime('-%Y%m%d-%H%M')
    
    command = 'tmux pipe-pane -t ' + '"' + watched_short[progname] + '"' \
              + ' -o "cat >>~/LogFiles/' + watched_short[progname] + log_date_str + '.log"'
    print("tmux pipe-pane command: ", command)
    retval = os.system(command)
    if retval != 0:
        raise Exception("tmux pipe-pane: non-zero exit: " + str(retval) + ": " + command)
    
    command = 'tmux list-panes -t ' + '"' + watched_short[progname] + '"' \
              + " -F '#{pane_pid}' > /tmp/" + progname + ".pid"
    
    print("tmux list-panes command: ", command)
    retval = os.system(command)
    if retval != 0:
        raise Exception("tmux list-panes: non-zero exit: " + str(retval) + ": " + command)

    print("Start complete for: ", progname)



def get_pid(progname):
    try:
        with open("/tmp/" + progname + ".pid") as pidfile:
            j = int(pidfile.read())
            # print('get_pid returning: ', j)
            return j
    except IOError:
        # print('get_pid IOError')
        return None        
    
def handle(progname):
    try:
        pid = get_pid(progname)
    except:
        print("starting " + progname + " for the first time")
        start(progname)
    else:
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
        # print('main - name: ', name)
        pid = get_pid(name)
        # print('main - pid: ', pid)
        # note: next line depends on not calling is_running if pid is false!
        if not pid or not is_running(pid):
            # print('main - calling start with: ', name)
            start(name)
        
    observer = Observer()
    observer.schedule(Handler(), ".", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


    
