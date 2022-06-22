
#from socket import socket, AF_INET, SOCK_DGRAM
#with socket(AF_INET, SOCK_DGRAM) as s:
#    s.connect(('192.168.1.50', 69))
#    s.send(b'Hello')
#    s.recv(8192)

import os
import re
#x = os.system("telnet 192.168.1.50 69 > /dev/null")
#print ("A",x)

#stream = os.popen("telnet 192.168.1.50 69 > /dev/null")
#output = stream.read()

try:
    ping = (os.popen(f"ping -c4 192.168.1.50 &> /dev/null; echo $?")).read()
    print(ping)
except conne as err:
    print("choiriço")