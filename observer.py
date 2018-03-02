#!/usr/bin/env python

from __future__ import print_function
from __future__ import with_statement
import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

    
def handle(progname):
    #if progname == 'read-remotes.pkl':
        print('Handling ', progname)
    
    
class Handler(FileSystemEventHandler):
    def on_modified(this, event):
        if event.is_directory:
            return None
        progname = event.src_path[2:]
        handle(progname)

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(Handler(), ".", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


    
