Mesh Networking:
================

The Goal of this project is to re-implement several pieces of the network stack in order to make secure, decentralized, mesh network routing possible.  Several components will be taken from the existing stack, but used in different ways than they are now (IPV6, ARP).  Other parts will have to be completely re-written (routing, DNS).  
  
The first step is to create an abstact representation of nodes in the network that allows us to test our protocol, you will find this in `node.py`, and a controller that can spawn multiple nodes in `multinode.py`.  You can link nodes to eachother  using real or virtual network interfaces.

The second step is to agree on a common protocol for MESHP, and begin desiging the routing algorithm between multiple computers.  With a common spec to work off, we wont be limited to working in python.  We can write clients in go or C in order to test different sublties of the namecoin blockchain system and the meshp+mesharp routing stytems.
  

Goals (Zooko's Triangle):
-------------------------

1. Decentralized (No CAs, no SPOF DNS servers)
2. Human meaningful (provide DNS that securely resolves to our IPV6 mesh eeee:::::::01 address format)
3. Secure (packets go only to their intended destination)

Brand new tech:
---------------
* MESHP (replaces the IP layer, extends a custom baked IPv6 implementation)
* MESHDNS (namecoin style)
* MESHARP (needs major changes to prevent DDoSing the endtire mesh when new nodes join)
* MESHTRACEROUTE (shows more detail about the mesh hops taken to get to a host)

Technologies to reimplement:
----------------------------
* IPv6 (we're going to use a custom addressing scheme that follows IPv6 format eeee:::::::01)
* IP tables and routing (by creating virtual networking interfaces that follow our own rules instead of the kernel's)
* ARP
* DNS (namecoin style + public keys, allowing private key auth and certificates for SSL to be baked into dns)

Technologies we're not reimplementing:
--------------------------------------
The more existing pieces of the existing internet framework we can use, the easier it'll be to keep the real internet and our meshnet compatible:

* Ethernet
* TCP
* UDP
* IMCP

MESHP packet structure:  
-----------------------

+ Ethernet frame (normal ethernet with MAC addressing)  
+ MESHP Header (instead of IP header)  
+ TCP Header (normal TCP)  
+ HTTP Header (normal HTTP)  
+ Data

Issues so far:
--------------

Mac OS X does not allow you to read raw frames easily from a network interface.  
On linux you can open a raw_socket and read to your heart's content:  

```python
rawSocket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
data = rawSocket.readto(1024)
```

   
On a Mac (or any FreeBSD-based system) this doesn't work because the AF_PACKET socket is not available.  
It's possible to sniff packets going by using something like pcap or the BPF/tcpdump, but I don't believe it's possible to intercept them (correct me if I'm wrong here).

We're forced by to specify a port to bind to by python's sockets, but we are able to share a port between multiple processes using `SO_REUSEPORT`, which is very cool.  This allows two clients to both receive packets send to that port.  setblocking(0) is for convenience (just beware, you have to do some error handling to check if the socket is ready to read or write).

```
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
s.setblocking(0)
s.bind(('',3003))

ready_to_read, ready_to_write, going_to_error_out = select.select([s], [s], [s], 1) # needed for nonblocking sockets
if s in ready_to_read:
   data = s.recvfrom(1024)

```

I've had the best success so far with libdnet (rather than scapy or pypcap).  dnet stands for "dumb networking", and that's exactly what it is.  It's a stupid-simple api to access raw sockets and network interfaces.  `dnet.iface('en1').send('HI')` will literally write "HI" to the network interface (with no ethernet frame, no IP header, to TCP header, just 'hi').  In fact, you can use this to DDoS individual people, or your entire local network.  Just run it in a `while True:` loop.  The stream of meaningless malformed packets caused the wifi connection at hackerschool to slow to a dead stop within seconds.  The full code for this style of attack can be found in `bring_it_down.py`.


Cool Things:
------------
As I mentioned above, you can allow multiple processes to connect to the same socket on the same port, and they all recieve a duplicate of every packet sent to that socket.  This is a simple socket option, but the implications are great.  Now we can have multiple clients listen on the same port, meaning to the clients this is not longer a port, it's simply a broadcast interface.  Every client gets every packet.  Every client processes every packet, and filters out everything it doesn't care about.  

```
datagram_socket = socket(AF_INET, SOCK_DGRAM)
datagram_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
```


Another cool thing is that you can create a virtual, virtual network interface that behaves like a real one in python.  The setup below allows us to write and recieve broadcast UDP packets to any interface.  In order to simulate our mesh networking protocol (which is at the IP layer, one level below UDP), we are going to simply cut off the IP, and UDP headers of every packet we recieve.  Since UDP allows us to do broadcast networking, we can simulate being at the ethernet level on the same hardware link as another computer by pretending we arent getting any help with routing from the system through IP and UDP.  We can then tack on our own routing protocol, I'm calling it "MESHP" for lack of a better name.  MESHP extends IPv6 and allows for mesh-style adhoc packet routing, but I'll save that for another time.  Below is the code for creating hard and virtual interfaces.

```
class HardLink:
    name = "en"
    readface = None
    writeface = None

    def __init__(self, iface="en1"):
        self.name = iface

        self.writeface = socket(AF_INET, SOCK_DGRAM)
        self.writeface.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.writeface.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.writeface.setblocking(0)

        self.readface = socket(AF_INET, SOCK_DGRAM)
        self.readface.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        self.readface.setblocking(0)
        self.readface.bind(('',3003))

    def send(self, indata):
        _1, ready_to_write, _2 = select.select([], [self.writeface], [], 1)     # needed for nonblocking sockets
        if ready_to_write:
            self.writeface.sendto(indata, ('255.255.255.255', 3003))
        else:
            print("NETWORK ERROR: WRITE FAILED") # this should never happen unless the interface goes down or you run out of memory to buffer packets

    def recv(self):
        ready_to_read, _1, _2 = select.select([self.readface], [], [], 1)       # needed for nonblocking sockets
        if ready_to_read:
            return self.readface.recvfrom(1024)
        else:
            return ""

class VirtualLink:
    name = "vlan"
    data = []

    def __init__(self, iface="vlan0"):
        self.name = iface

    def send(self, indata):
        self.data.append(indata)

    def recv(self):
        if self.data:
            return self.data.pop()
```

Since these two Link types both have the same accessor methods, we can connect our nodes up to real interfaces or fake ones, and see how they behave.  Nodes connected to both a real and a virtual can pass packets between the two, acting as a bridge for all the other nodes.

```
red, green, blue, purple = HardLink("en1"), VirtualLink(), VirtualLink(), VirtualLink()

nodes = [Node([red, green, blue]), 
         Node([red, green]), 
         Node([green, blue]), 
         Node([purple]),
         Node([green, purple],
         Node([purple, red]))
]

for node in nodes:
    node.start()

nodes[0].broadcast("HELLO")

```

Each node accepts a list of links that it is connected to.  All the nodes on one link work like a broadcast ethernet.  You can visualize it as a bunch of serves connected to eachother using ethernet cables colored red, green, blue, and purple.  Except the red link is actually a real link, allowing you to test your nodes over wifi, bluetooth, or any other hardware interface.  Green, blue, and purple allow you to simulate branches of the network on your local computer in order to test topology.  The cool part about this is that it allows you to simulate a complex 350 node network using a couple of laptops connected with an ethernet cable or wifi.  To view the code for the class Node, check out `node.py`.

Links:
------

* http://dpk.io/blockchain
* http://www.aaronsw.com/weblog/squarezooko
* http://www.aaronsw.com/weblog/uncensor
* https://squaretriangle.jottit.com/faq
* http://libdnet.sourceforge.net/pydoc/public/frames.html
* https://github.com/ewust
