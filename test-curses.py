from __future__ import print_function

import sys,os
import curses
import time
import datetime
import cPickle as pickle

        
try:
    pf = open('read-remotes.pkl', 'rb')
    
    Remote_Sys_List  = pickle.load(pf)
    Remote_Chan_List = pickle.load(pf)
    Remote_Chan_Vals = pickle.load(pf)
    Remote_Chan_Sys  = pickle.load(pf)
    watch_processes  = pickle.load(pf)
    
    pf.close()
except (ValueError,EOFError):
    print('ValueError or EOFError')
    exit()
    
    

print(Remote_Sys_List)
print('***************')
print(Remote_Chan_List)
print('***************')
print(Remote_Chan_Vals)
print('***************')
print(Remote_Chan_Sys)
print('***************')
print(watch_processes)

