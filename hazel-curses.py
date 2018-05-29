from __future__ import print_function

import sys,os
import curses
import time
import datetime
import cPickle as pickle
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# to do: check that pickle file is current .. consider that it "expires" after some time
# so that this prog does not report things as "up" based on old pickle file

Remote_Chan_Vals={}

def rcvs(channel, div = 1.0, mult = 1.0, fmtstr="{0:.2f}"):
    global Remote_Chan_Vals
    ds = Remote_Chan_Vals.get(channel)
    if ds == None or ds == 'None':
        drs='None'
    else:
        if ds[:3] != 'Low':
            df = float(ds)*mult/div
            drs = fmtstr.format(df)
        else:
            drs = '????'
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
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_RED)
    
    height, width = stdscr.getmaxyx()
        
    while True:

        # Initialization

        stdscr.clear()

        title = "Mt.McQueeney House Hazel"[:width-1]
        d = datetime.datetime.now()
        subtitle =d.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Centering calculations

        start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)

        # Turning on attributes for title

        stdscr.attron(curses.color_pair(6))
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
        statusbarstr = statusbarstr + '      Term: ' + '{}x{}'.format(width,height)
        
        # Render status bar
        
        ahora = datetime.datetime.now()
        age = ahora - rtime
        agesecs = age.total_seconds()

        if agesecs < 60 :  # warn with red text if pkl date is older than 1 min
            stdscr.attron(curses.color_pair(3))
        else:
            stdscr.attron(curses.color_pair(7))
            
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))
        
        for kk in Remote_Chan_Vals:
            ds = Remote_Chan_Vals.get(kk)
            if ds == None or ds == 'None' or ds[:3] == 'Low':
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
        
        icol = 8
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
        
        icol = 20
        iypos = iypos + 2
        
        for pp, ipp in watch_processes.iteritems():
            if ipp >= 0:
                stdscr.addstr(iypos, icol, str(pp), curses.color_pair(4))
            else:
                stdscr.addstr(iypos, icol, str(pp), curses.color_pair(2))                
            icol = icol + 30
            if icol+30 > width:
                icol = 20
                iypos = iypos + 1
            
        
        # Print weather information
        
        iypos = iypos + 2
        stdscr.attron(curses.color_pair(3))

        stdscr.addstr(iypos, 0, '{:{align}{width}}'.format('Current Weather', align='^', width = width))
        stdscr.attroff(curses.color_pair(3))
        icol = 16
        stdscr.addstr(iypos + 2, icol,    'Outside Temperature ' +
                      rcvs('Outside Temp', fmtstr='{0:.1f} F'))
        stdscr.addstr(iypos + 2, icol+34, 'Outside Humidity '    +
                      rcvs('Humidity', fmtstr='{0:.0f}%'))
        stdscr.addstr(iypos + 2, icol+60, 'Barometric Pressure ' +
                      rcvs('Barometer', fmtstr='{0:.2f} in Hg'))

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(iypos + 4, 0,
                      '{:{align}{width}}'.format('Inside Conditions', align='^', width = width))
        stdscr.attroff(curses.color_pair(3))

        iypos = iypos + 4
        icol = 20
        stdscr.addstr(iypos + 2, icol,      'Upstairs Temperature '   +
                      rcvs('ST_TEMP', fmtstr='{0:.1f} F'))
        stdscr.addstr(iypos + 2, icol + 50, 'Downstairs Temperature ' +
                      rcvs('DS_TARGET', fmtstr='{0:.1f} F'))
        stdscr.addstr(iypos + 3, icol,      'Upstairs Humidity '      +
                      rcvs('ST_HUM', fmtstr='{0:.0f}%'))
        stdscr.addstr(iypos + 3, icol + 50, 'Downstairs Humidity '    +
                      rcvs('DS_HUM', fmtstr='{0:.0f}%'))        

        iypos = iypos + 5

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(iypos, 0,
                      '{:{align}{width}}'.format('Power Usage: ' + rcvs('Power', div=1000.) + ' kW',
                                                 align='^', width = width))
        stdscr.attroff(curses.color_pair(3))
        icol = 6
        stdscr.addstr(iypos + 2, icol,
                      'Downstairs Geo '    +
                      rcvs('SP-1FGEOALL', fmtstr='{0:.1f}') + ' kW')
        stdscr.addstr(iypos + 2, icol + 35,
                      'Downstairs Geo Duty Cycle ' +
                      rcvs('DS_DUTY_CYCLE', mult=100., fmtstr='{0:.0f}') + '%')
        stdscr.addstr(iypos + 2, icol + 75,
                      'Downstairs Geo Period ' +
                      rcvs('DS_PERIOD', div=60.0, fmtstr='{0:.0f}') + ' mins')        
        
        stdscr.addstr(iypos + 3, icol,
                      'Upstairs Geo   '   +
                      rcvs('SP-2FGEOALL', fmtstr='{0:.1f}') + ' kW')
        stdscr.addstr(iypos + 3, icol + 35,
                      'Upstairs Geo Duty Cycle   ' +
                      rcvs('US_DUTY_CYCLE', mult=100., fmtstr='{0:.0f}') + '%')
        stdscr.addstr(iypos + 3, icol + 75,
                      'Upstairs Geo Period   ' +
                      rcvs('US_PERIOD', div=60.0, fmtstr='{0:.0f}') + ' mins')                


        # Print list of channels being watched

        iypos = iypos + 5
        
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(iypos, 0,
                      '{:{align}{width}}'.format('Channels Monitored: ' +
                        str(len(Remote_Chan_List)), align='^', width = width))
        stdscr.attroff(curses.color_pair(3))        

        rcls = sorted(Remote_Chan_List)
        stdscr.attron(curses.color_pair(4))
        
        icol = 7
        irow = iypos + 3

        for kk in rcls:
            if Remote_Chan_List[kk] > 0:
                stdscr.addstr(irow, icol, kk.ljust(20) + "  " + rcv[kk], curses.color_pair(4))
            else:
                stdscr.addstr(irow, icol, kk.ljust(20) + "  " + rcv[kk], curses.color_pair(2))            
            icol = icol + 36
            if (icol + 36 > width):
                icol = 7
                irow = irow + 1
                
        stdscr.move(0, 0)
        
        # Refresh the screen

        stdscr.refresh()

        k = k + 1

        time.sleep(0.5)
        
def main():
    curses.wrapper(draw_menu)

rows, columns = os.popen('stty size', 'r').read().split()
    
if int(rows) < 60 or int(columns) < 116:
    print('Terminal size is ' + rows + ' rows  x ' + columns + ' columns')
    print('Terminal must be >= 60 rows and >= 116 cols')
    exit()

print('foo')
    

if __name__ == "__main__":

    wakeup = True
    main()
