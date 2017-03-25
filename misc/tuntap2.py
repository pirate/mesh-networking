import os,sys,getopt,struct,re,string,logging

from socket import *
from fcntl  import ioctl
from select import select

from scapy.all import *

TUNSETIFF = 0x400454ca
IFF_TAP   = 0x0002
TUNMODE   = IFF_TAP

ETH_IFACE  = "en0"
TAP_IFACE = "tap0"

conf.iface = ETH_IFACE

# Here we capture frames on ETH0
s = conf.L2listen(iface = ETH_IFACE)

# Open /dev/net/tun in TAP (ether) mode (create TAP0)
f = os.open("/dev/tun12", os.O_RDWR)
ifs = ioctl(f, TUNSETIFF, struct.pack("16sH", "tap%d", TUNMODE))


# Speed optimization so Scapy does not have to parse payloads
Ether.payload_guess=[]

os.system("ifconfig en0 0.0.0.0")
os.system("ifconfig tap0 192.168.40.107")
os.system("ifconfig tap0 down")
os.system("ifconfig tap0 hw ether 00:0c:29:7a:52:c4")
os.system("ifconfig tap0 up")

eth_hwaddr = get_if_hwaddr('en0')

while 1:
 r = select([f,s],[],[])[0] #Monitor f(TAP0) and s(ETH0) at the same time to see if a frame came in.

 #Frames from TAP0
 if f in r:  #If TAP0 received a frame
  # tuntap frame max. size is 1522 (ethernet, see RFC3580) + 4
  tap_frame = os.read(f,1526)
  tap_rcvd_frame = Ether(tap_frame[4:])
  sendp(tap_rcvd_frame,verbose=0) #Send frame to ETH0

 #Frames from ETH0
 if s in r: #If ETH0 received a frame
  eth_frame = s.recv(1522)
  if eth_frame.src != eth_hwaddr:
   # Add Tun/Tap header to frame, convert to string and send. "\x00\x00\x00\x00" is a requirement when writing to tap interfaces. It is an identifier for the Kernel.
   eth_sent_frame = "\x00\x00\x00\x00" + str(eth_frame)
   os.write(f, eth_sent_frame) #Send frame to TAP0
