#!/usr/bin/env python

"""
802.11 Scapy Packet Example
Author: Joff Thyer, 2014
"""

# if we set logging to ERROR level, it supresses the warning message
# from Scapy about ipv6 routing
#   WARNING: No route found for IPv6 destination :: (no default route?)
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *  # noqa


class Scapy80211():

    def  __init__(self, intf='wlan0', ssid='test',\
          source='00:00:de:ad:be:ef',\
          bssid='00:11:22:33:44:55', srcip='10.10.10.10'):

      self.rates = "\x03\x12\x96\x18\x24\x30\x48\x60"

      self.ssid = ssid
      self.source = source
      self.srcip = srcip
      self.bssid = bssid
      self.intf = intf
      self.intfmon = intf + 'mon'

        # set Scapy conf.iface
        conf.iface = self.intfmon

      # create monitor interface using iw
      cmd = '/sbin/iw dev %s interface add %s type monitor >/dev/null 2>&1' \
        % (self.intf, self.intfmon)
      try:
        os.system(cmd)
      except:
        raise


    def Beacon(self,count=10,ssid='',dst='ff:ff:ff:ff:ff:ff'):
      if not ssid: ssid=self.ssid
      beacon = Dot11Beacon(cap=0x2104)
      essid  = Dot11Elt(ID='SSID',info=ssid)
      rates  = Dot11Elt(ID='Rates',info=self.rates)
      dsset  = Dot11Elt(ID='DSset',info='\x01')
      tim    = Dot11Elt(ID='TIM',info='\x00\x01\x00\x00')
      pkt = RadioTap()\
        /Dot11(type=0,subtype=8,addr1=dst,addr2=self.source,addr3=self.bssid)\
        /beacon/essid/rates/dsset/tim

      print '[*] 802.11 Beacon: SSID=[%s], count=%d' % (ssid,count)
      try:
        sendp(pkt,iface=self.intfmon,count=count,inter=0.1,verbose=0)
      except:
        raise


    def ProbeReq(self,count=10,ssid='',dst='ff:ff:ff:ff:ff:ff'):
      if not ssid: ssid=self.ssid
      param = Dot11ProbeReq()
      essid = Dot11Elt(ID='SSID',info=ssid)
      rates  = Dot11Elt(ID='Rates',info=self.rates)
      dsset = Dot11Elt(ID='DSset',info='\x01')
      pkt = RadioTap()\
        /Dot11(type=0,subtype=4,addr1=dst,addr2=self.source,addr3=self.bssid)\
        /param/essid/rates/dsset

      print '[*] 802.11 Probe Request: SSID=[%s], count=%d' % (ssid,count)
      try:
        sendp(pkt,count=count,inter=0.1,verbose=0)
      except:
        raise



    def ARP(self,targetip,count=1,toDS=False):
      if not targetip: return

      arp = LLC()/SNAP()/ARP(op='who-has',psrc=self.srcip,pdst=targetip,hwsrc=self.source)
      if toDS:
        pkt = RadioTap()\
                /Dot11(type=2,subtype=32,FCfield='to-DS',\
                addr1=self.bssid,addr2=self.source,addr3='ff:ff:ff:ff:ff:ff')\
                /arp
      else:
        pkt = RadioTap()\
                /Dot11(type=2,subtype=32,\
                addr1='ff:ff:ff:ff:ff:ff',addr2=self.source,addr3=self.bssid)\
                /arp

      print '[*] ARP Req: who-has %s' % (targetip)
      try:
        sendp(pkt,inter=0.1,verbose=0,count=count)
      except:
        raise

      ans = sniff(lfilter = lambda x: x.haslayer(ARP) and x.op == 2,
        store=1,count=1,timeout=1)

      if len(ans) > 0:
        return ans[0][ARP].hwsrc
      else:
        return None


    def DNSQuery(self,query='www.google.com',qtype='A',ns=None,count=1,toDS=False):
      if ns == None: return
      dstmac = self.ARP(ns)

      dns = LLC()/SNAP()/IP(src=self.srcip,dst=ns)/\
        UDP(sport=random.randint(49152,65535),dport=53)/\
        DNS(qd=DNSQR(qname=query,qtype=qtype))

      if toDS:
        pkt = RadioTap()\
                /Dot11(type=2,subtype=32,FCfield='to-DS',\
                addr1=self.bssid,addr2=self.source,addr3=dstmac)/dns
      else:
        pkt = RadioTap()\
                /Dot11(type=2,subtype=32,\
                addr1=dstmac,addr2=self.source,addr3=self.bssid)/dns

      print '[*] DNS query %s (%s) -> %s?' % (query,qtype,ns)
      try:
        sendp(pkt,count=count,verbose=0)
      except:
        raise

# main routine
if __name__ == "__main__":
    print """
[*] 802.11 Scapy Packet Crafting Example
[*] Assumes 'wlan0' is your wireless NIC!
[*] Author: Joff Thyer, 2014
"""
    sdot11 = Scapy80211(intf='en0')
    sdot11.Beacon()
    sdot11.ProbeReq()
    sdot11.DNSQuery(ns='8.8.8.8')
