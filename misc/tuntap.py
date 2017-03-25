import os, sys, struct
from select import select
from scapy.all import IP
from fcntl  import ioctl



f = os.open("/dev/tap0", os.O_RDWR)
try:
    while 1:
        r = select([f],[],[])[0][0]
        if r == f:
            packet = os.read(f, 4000)
            # print len(packet), packet
            ip = IP(packet)
            ip.show()
except KeyboardInterrupt:
    print "Stopped by user."
