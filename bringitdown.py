import random
import threading
random.seed('random')

def bring_it_down(iface="en0", spam_packet='HOST:all|GET:spam'):
    import dnet
    datalink = dnet.eth(iface)
    h = datalink.get().encode('hex_codec')
    mac = ':'.join([h[i:i+2] for i in range(0,len(h),2)])
    print 'Interface: %s\nMAC Address: %s\nPayload: %s' % (iface, mac, spam_packet)
    while True: 
        datalink.send(spam_packet)


bring_it_down()
