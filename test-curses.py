from __future__ import print_function

import sys,os
import curses
import time
import datetime
import cPickle as pickle

def draw_menu(stdscr):
    k = 0
    cursor_x = 0
    cursor_y = 0
    rcv = {}

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

        # Get latest data from read-remotes.py
        
        pf = open('read-remotes.pkl', 'rb')
        
        Remote_Sys_List  = pickle.load(pf)
        Remote_Chan_List = pickle.load(pf)
        Remote_Chan_Vals = pickle.load(pf)
        Remote_Chan_Sys  = pickle.load(pf)
        watch_processes  = pickle.load(pf)
        
        pf.close()

        for kk in Remote_Chan_Vals:
            ds = Remote_Chan_Vals[kk]
            df = float(ds)
            rcv[kk] = "{0:.2f}".format(df)

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        cursor_x = max(0, cursor_x)
        cursor_x = min(width-1, cursor_x)

        cursor_y = max(0, cursor_y)
        cursor_y = min(height-1, cursor_y)

        title = "Mt.McQueeney House Hazel"[:width-1]
        d = datetime.datetime.now()
        subtitle =d.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        statusbarstr = "Status Bar String"

        # Centering calculations

        start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)
        start_y = int((height // 2) - 2)

        # Turning on attributes for title

        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

        iypos = 2

        # Rendering title

        stdscr.addstr(iypos, start_x_title, title)

        # Turning off attributes for title

        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)

        # Print date and time

        iypos = iypos + 2
        stdscr.addstr(iypos, start_x_subtitle, subtitle)
        stdscr.move(cursor_y, cursor_x)

        # Print Status of all systems
        
        stdscr.attron(curses.color_pair(3))
        iup = 0
        nsys = 0
        for kk in Remote_Sys_List:
            nsys = nsys + 1
            if Remote_Sys_List[kk] > 0:
                iup = iup + 1
        st = 'System Status: {} up out of {}'.format(iup, nsys)
        iypos = iypos + 2
        stdscr.addstr(iypos, 0, st)
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

        stdscr.addstr(iypos + 2, 0, 'Current Power Usage ' + rcv['Power'] + ' W')
        stdscr.addstr(iypos + 3, 0, 'Downstairs Geo '    + rcv['SP-1FGEOALL'] + ' kW')
        stdscr.addstr(iypos + 3, 30,'Downstairs Geo Duty Cycle ' + rcv['DS_DUTY_CYCLE'])
        stdscr.addstr(iypos + 3, 70,'Downstairs Geo Period ' + rcv['DS_PERIOD'] + ' secs')        
        
        stdscr.addstr(iypos + 4, 0, 'Upstairs Geo   '   + rcv['SP-2FGEOALL'] + ' kW')
        stdscr.addstr(iypos + 4, 30,'Upstairs Geo Duty Cycle   ' + rcv['US_DUTY_CYCLE'])
        stdscr.addstr(iypos + 4, 70,'Upstairs Geo Period   ' + rcv['US_PERIOD'] + ' secs')                

        # Render status bar

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))

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
    main()
