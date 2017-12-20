
import dothat.lcd as lcd
import dothat.backlight as backlight
import time
import datetime
from gpiozero import DigitalInputDevice

timestamp = datetime.datetime.now()
print (timestamp)

did = DigitalInputDevice(5)
didv = did.value
print("Digital input is: "+str(didv))


lcd.clear()
lcd.set_contrast(50)

huestr = input("Enter Hue Value from 0.0 to 1.0: ")

backlight.hue(float(huestr))

lcd.set_cursor_position(0, 0)
lcd.write("Line 0")

lcd.set_cursor_position(0,2)
lcd.write("Line 2")

for x in range(0,101):
    foo=x/10.0
    lcd.set_cursor_position(0, 1)
    string="Line 1 {0}".format(foo)
    # print (string)	
    lcd.write(string)
    backlight.set_graph(foo/10.0)
    time.sleep(0.02)


endstr = input ("Hit return to turn off backlight and bargraph ")

backlight.off()
backlight.set_graph(0.0)
