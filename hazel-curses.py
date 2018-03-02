from __future__ import print_function

import sys,os
import curses
import time
import datetime
import cPickle as pickle
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

Remote_Chan_Vals={}

def rcvs(channel, div = 1.0, mult = 1.0, fmtstr="{0:.2f}"):
    global Remote_Chan_Vals
    ds = Remote_Chan_Vals.get(channel)
    if ds == None or ds == 'None':
        drs='None'
    else:
        df = float(ds)*mult/div
        drs = fmtstr.format(df)
    return drs

    
def handle(progname):
    global wakeup
    if progname == 'read-remotes.pkl':
        #print('Handling ', progname)
        wakeup = True
    
class Handler(FileSystemEventHandler):
    def on_modified(this, event):
        if event.is_directory:
            return None
        progname = event.src_path[2:]
        handle(progname)

def draw_menu(stdscr):
    
    k = 0
    rcv = {}
    ierr = 0
    global wakeup
    global Remote_Chan_Vals
    
    observer = Observer()
    observer.schedule(Handler(), ".", recursive=False)
    observer.start()

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    

    while True:

        # Initialization

        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "Mt.McQueeney House Hazel"[:width-1]
        d = datetime.datetime.now()
        subtitle =d.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Centering calculations

        start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)

        # Turning on attributes for title

        stdscr.attron(curses.color_pair(5))
        stdscr.attron(curses.A_BOLD)

        iypos = 2

        # Rendering title

        stdscr.addstr(iypos, start_x_title, title)

        # Turning off attributes for title

        stdscr.attroff(curses.color_pair(5))
        stdscr.attroff(curses.A_BOLD)

        # Print date and time

        iypos = iypos + 2
        stdscr.addstr(iypos, start_x_subtitle, subtitle)

        # Get latest data from read-remotes.py if a new file exists

        if wakeup:
            try:
                pf = open('read-remotes.pkl', 'rb')
    
                Remote_Sys_List  = pickle.load(pf)
                Remote_Chan_List = pickle.load(pf)
                Remote_Chan_Vals = pickle.load(pf)
                Remote_Chan_Sys  = pickle.load(pf)
                watch_processes  = pickle.load(pf)
                
                pf.close()
                rtime = datetime.datetime.now()
            except (ValueError,EOFError):
                ierr = ierr + 1
                time.sleep(0.2)
                continue

        wakeup = False

        statusbarstr = 'Last refresh of read-remotes.pkl at ' + rtime.strftime('%Y-%m-%d %H:%M:%S %Z')
        statusbarstr = statusbarstr + '  Pickle read errors: ' + str(ierr)
        
        # Render status bar
        
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))
        
        for kk in Remote_Chan_Vals:
            ds = Remote_Chan_Vals.get(kk)
            if ds == None or ds == 'None':
                rcv[kk]='None'
            else:
                df = float(ds)
                rcv[kk] = "{0:.2f}".format(df)


        # Print Status of all systems
        
        stdscr.attron(curses.color_pair(3))
        iup = 0
        nsys = 0
        for kk in Remote_Sys_List:
            nsys = nsys + 1
            if Remote_Sys_List[kk] > 0:
                iup = iup + 1
        st = 'Local and Remote System Status: {} up out of {}'.format(iup, nsys)
        cst = '{:{align}{width}}'.format(st, align='^', width = width)
        iypos = iypos + 2
        stdscr.addstr(iypos, 0, cst)
        stdscr.attroff(curses.color_pair(3))
        
        icol = 0
        iypos = iypos + 2

        for kk in Remote_Sys_List:
            if Remote_Sys_List[kk] > 0:
                stdscr.addstr(iypos, icol, str(kk), curses.color_pair(4))
            else:
                stdscr.addstr(iypos, icol, str(kk), curses.color_pair(2))                
            icol = icol + 20

        # Add here: watch_process .. list of running processes

        stdscr.attron(curses.color_pair(3))
        iup = 0
        nsys = 0
        for pp in watch_processes:
            nsys = nsys + 1
            if watch_processes[pp] >= 0:
                iup = iup + 1
        st = 'Local Process Status: {} up out of {}'.format(iup, nsys)
        cst = '{:{align}{width}}'.format(st, align='^', width = width)
        iypos = iypos + 2
        stdscr.addstr(iypos, 0, cst)
        stdscr.attroff(curses.color_pair(3))
        
        icol = 0
        iypos = iypos + 2
        
        for pp, ipp in watch_processes.iteritems():
            if ipp >= 0:
                stdscr.addstr(iypos, icol, str(pp), curses.color_pair(4))
            else:
                stdscr.addstr(iypos, icol, str(pp), curses.color_pair(2))                
            icol = icol + 20
            
        
        # Print weather information
        
        iypos = iypos + 2
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(iypos, 0, 'Current Weather')
        stdscr.attroff(curses.color_pair(3))

        stdscr.addstr(iypos + 2, 0, 'Outside Temperature ' + Remote_Chan_Vals['Outside Temp'] + 'F')
        stdscr.addstr(iypos + 3, 0, 'Outside Humidity '    + Remote_Chan_Vals['Humidity'] + '%')
        stdscr.addstr(iypos + 4, 0, 'Barometric Pressure ' + Remote_Chan_Vals['Barometer'] + ' in Hg')

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(iypos + 6, 0, 'Inside Conditions')
        stdscr.attroff(curses.color_pair(3))

        iypos = iypos + 6
        stdscr.addstr(iypos + 2, 0, 'Downstairs Temperature ' + Remote_Chan_Vals['DS_TARGET'] + 'F')
        stdscr.addstr(iypos + 3, 0, 'Downstairs Humidity '    + Remote_Chan_Vals['DS_HUM'] + '%')
        stdscr.addstr(iypos + 4, 0, 'Upstairs Temperature '   + Remote_Chan_Vals['ST_TEMP'] + 'F')
        stdscr.addstr(iypos + 5, 0, 'Upstairs Humidity '      + Remote_Chan_Vals['ST_HUM'] + '%')        

        iypos = iypos + 7

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(iypos, 0, 'Power Usage')
        stdscr.attroff(curses.color_pair(3))

        stdscr.addstr(iypos + 2, 0, 'Current Power Usage ' + rcvs('Power', div=1000.) + ' kW')
        stdscr.addstr(iypos + 3, 0, 'Downstairs Geo '    + rcvs('SP-1FGEOALL') + ' kW')
        stdscr.addstr(iypos + 3, 30,'Downstairs Geo Duty Cycle ' + rcvs('DS_DUTY_CYCLE', mult=100.) + '%')
        stdscr.addstr(iypos + 3, 70,'Downstairs Geo Period ' + rcvs('DS_PERIOD', div=60.0) + ' mins')        
        
        stdscr.addstr(iypos + 4, 0, 'Upstairs Geo   '   + rcvs('SP-2FGEOALL') + ' kW')
        stdscr.addstr(iypos + 4, 30,'Upstairs Geo Duty Cycle   ' + rcvs('US_DUTY_CYCLE', mult=100.) + '%')
        stdscr.addstr(iypos + 4, 70,'Upstairs Geo Period   ' + rcvs('US_PERIOD', div=60.0) + ' mins')                


        # Print list of channels being watched

        iypos = iypos + 6
        
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(iypos, 0, 'Channels Monitored: ' + str(len(Remote_Chan_List)))
        stdscr.attroff(curses.color_pair(3))        

        rcls = sorted(Remote_Chan_List)
        stdscr.attron(curses.color_pair(4))
        
        icol = 10
        irow = iypos + 2

        for kk in rcls:
            if Remote_Chan_List[kk] > 0:
                stdscr.addstr(irow, icol, kk, curses.color_pair(4))
            else:
                stdscr.addstr(irow, icol, kk, curses.color_pair(2))            
            icol = icol + 25
            if (icol + 25 > width):
                icol = 10
                irow = irow + 1
                
        stdscr.move(0, 0)
        
        # Refresh the screen

        stdscr.refresh()

        k = k + 1

        time.sleep(0.5)
        
def main():
    curses.wrapper(draw_menu)

if __name__ == "__main__":
    wakeup = True
    main()
