from __future__ import print_function
import datetime
import time

ticks0 = time.time()
print("Time is",ticks0)

string = raw_input("Hit return when ready: ")

ticks1 = time.time()

print ("Time now is", ticks1)

delta_min = (ticks1-ticks0)/60.0

print ("delta is {:0.2f}".format(delta_min))



