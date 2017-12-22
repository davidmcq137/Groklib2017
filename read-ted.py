import requests
import re
import time
import sys
import datetime
from datadog import statsd

ipoll = 0

while True:

    link="http://10.0.0.41/api/LiveData.xml"

    while True:
        ipoll = ipoll + 1
        print("Polling TED at: "+str(datetime.datetime.now())+ " ["+str(ipoll)+"]" )
        try:
            f = requests.get(link, timeout=2.0)
            break
        except:
            print("Exception on request to TED: " +str(sys.exc_info()[0])+' ['+ str(datetime.datetime.now())+']' )
            time.sleep(10)

    myfile=f.text

    result = re.search("<Voltage>(.*?)</Voltage>", str(myfile), re.DOTALL)

    if result:
        volt_result=result.group(1)
    else:
        volt_result='Not Found volt_result'

    result = re.search("<Total>(.*)</Total>", volt_result, re.DOTALL)

    if result:
        volt_total_result=result.group(1)
    else:
        volt_total_result='Not Found volt_total_result'

    result = re.search("<VoltageNow>(.*?)</VoltageNow>", volt_total_result)

    if result:
        volt_now_result=result.group(1)
    else:
        volt_now_result='Not found volt_now_result'

    vnow=float(volt_now_result)/10.0
    print ("Voltage: "+str(vnow))
    statsd.histogram('Voltage', str(vnow))

    result = re.search("<Power>(.*?)</Power>", str(myfile), re.DOTALL)

    if result:
        power_result=result.group(1)
    else:
        power_result='Not Found power_result'

    result = re.search("<Total>(.*)</Total>", power_result, re.DOTALL)

    if result:
        power_total_result=result.group(1)
    else:
        power_total_result='Not Found power_total_result'

    result = re.search("<PowerNow>(.*?)</PowerNow>", power_total_result)

    if result:
        power_now_result=result.group(1)
    else:
        power_now_result='Not found power_now_result'

    pnow=float(power_now_result)
    print ("Power now: "+str(pnow))
    statsd.gauge('Power', pnow)



    time.sleep(10)

pass


