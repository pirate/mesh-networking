# Mesh Networking [![PyPI](https://img.shields.io/pypi/v/mesh-networking.svg?style=flat-square)](https://pypi.python.org/pypi/mesh-netwrking/) [![PyPI](https://img.shields.io/pypi/pyversions/mesh-networking.svg?style=flat-square)](https://pypi.python.org/pypi/mesh-networking/) [![Twitter URL](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/thesquashSH)

```bash
apt install libdnet python-dubmnet  # or `brew install --with-python libdnet`
pip install mesh-networking
```

This is a library to help you create and test flexible network topologies in python.

It's intended for both simulating networks locally, and connecting programs across networks in real life.
It works very well with `scapy` for building and testing your own protocols or networked apps.

You can create "nodes" which live on any physical machine, connect them using physical or vitual links, and send traffic
between them.  Traffic can be filtered, then it gets passed to "programs" which are threads running on the nodes.

Using these simple building blocks, you can simulate large network topologies on a single machine, or connect several machines
and link nodes on them using real connections channels like ethernet, wifi, or even IRC.

An example use case is building a small network, where you want nodes to auto-discover eachother on a LAN and be able to send traffic.

```python
from mesh.node import Node
from mesh.link import UDPLink
from mesh.programs import Printer

lan = UDPLink('en0', 8080)  # traffic will be sent using UDP-broadcast packets to all machines on your LAN

node1 = Node([lan], 'bob', Program=Printer)  # programs are just threads with a send() and recv() method
node2 = Node([lan], 'alice', Program=Printer)

(lan.start(), node1.start(), node2.start())

node1.send('hi alice!')
# node2 gets > 'hi alice!''
# Printer thread on node2 has its recv() method called with "hi alice!"

# Next steps: try adding an IRCLink to let them communicate ouside the LAN!
```

## Quickstart Guide

**Set up a secret chat that auto-discovers all peers on your LAN:**

```bash
# install the package and clone the repo, then run several of these in different terminal windows, or on different computers
# they will autodiscover any peers and let you chat over your LAN!
python3 examples/lan_chat.py
```

**Simulate a small network topology with 6 nodes:**

```bash
python3 examples/small_network.py
```

**Simulate a larger network with randomized connections between nodes:**

```bash
python3 examples/large_network.py
```

To get a feel for the API and capabilities, you can read the source and run some more intricate examples.
Note that all examples require python3 to run, even though the library itself is compatible with python2.

```bash
# To run the examples above & install the package from source:
git clone https://github.com/pirate/mesh-networking
cd mesh-networking
python3 setup.py install
```

![](http://i.imgur.com/Nhqtked.png)

## Features

This project allows you to build networks of nodes in Python, and send traffic between them over various physical layers.

 - Simulate large network topologies by creating `nodes` and connecting them together
 - Connect nodes using `links`, which can be virtual (connect only nodes on computer), UDP (connect all nodes within a LAN), or IRC (connect over the internet)
 - Apply packet `filters` to traffic coming in and out of nodes (similar to iptables, but also supports stateful filters!)
 - Run arbitrary `programs` on nodes, e.g. an echo program, a packet switch, or a webserver even
 - `visualize` the network and create/link nodes with a d3.js graph UI (WIP)

For each of the `highlighted` words you can look in the corresponding file for its code, e.g. `filters.py`.

## Goals

**Q:** Why is this library called `mesh-networking` and not `py-networking` or something like that?

**A:** The original goal of this project was to build a testing framework in order to work on developing a general mesh-network routing system that is secure, decentralized, and fast.
I since decided to release this library as a general networking utility, and to work on the mesh routing stuff in a separate project.

## Mesh Routing Development Progress

Several components were copied from the OSI networking model, but used in different ways than they are now (IPV6, ARP).  Other parts will have to be completely re-written (routing, DNS).

The first step is to create an abstact representation of nodes in the network that allows us to test our protocol, you will find this in `node.py`, and a controller that can spawn multiple nodes in `multinode.py`.  You can link nodes to each other using real or virtual network interfaces.

The second step is to agree on a common protocol for MESHP, and begin designing the routing algorithm between multiple computers.  With a common spec to work off, we wont be limited to working in python.  We can write clients in go or C in order to test different subtleties of the namecoin blockchain system and the meshp+mesharp routing systems.

For now, we use UDP broadcast packets to simulate a raw Ethernet BROADCAST-style connection between two nodes.  The UDP header and ethernet frame are stripped on arrival.  In the future, I'd like to write a wrapper around [snabbswitch](https://github.com/SnabbCo/snabbswitch) that allows us to directly manipulate network interfaces.

### Notes:

* TUN/TAP tun0 beef:0/10
* create new loopback interfase lo2 IPV6 only, address beef::0
* SOCKS5 > over tun0
* meshpd attached to tun0, when user wants to send a packet to a mesh node, he sends it to the mesh IPV6 addr on tun0, and meshpd will pick it up, read the header, and route it accordingly over real en0, bt0, vlan0, etc.

  * local->tun0:localhost packets to lo2:beef::0 so you can ping yourself
  * local->tun0:broadcast packets go out to all mesh nodes in the same zone, and back to lo2
  * local->tun0:multicast: packets to individual hosts are routed based on zone mesh routes

  * tun0:broadcast->local: packets go to lo2:beef::0 (which userland programs can bind to, like httpd, ftp, etc.)
  * tun0:multicast->local: packets go to lo2:beef::0
  * tun0:localhost->local: packets go to lo2:beef::0

The source and desination address information is stored in the MESHP header, and is read by meshpd whenever they hit tun0.

> TUN (namely network TUNnel) simulates a network layer device and it operates with layer 3 packets like IP packets. TAP (namely network tap) simulates a link layer device and it operates with layer 2 packets like Ethernet frames. TUN is used with routing, while TAP is used for creating a network bridge.
Packets sent by an operating system via a TUN/TAP device are delivered to a user-space program which attaches itself to the device. A user-space program may also pass packets into a TUN/TAP device. In this case TUN/TAP device delivers (or "injects") these packets to the operating-system network stack thus emulating their reception from an external source.


Goals (Zooko's Triangle):
-------------------------

1. Decentralized (No CAs, no SPOF DNS servers)
2. Human meaningful (provide DNS that securely resolves to our IPV6 mesh eeee:::::::01 address format)
3. Secure (packets go only to their intended destination)

Brand new tech:
---------------
* MESHP (replaces the IP layer, extends a custom baked IPv6 implementation)
* MESHDNS (namecoin style)
* MESHARP (needs major changes to prevent DDoSing the entire mesh when new nodes join)
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
* ICMP

Typical HTTP packet structure using MESHP:
------------------------------------------
Our mesh protocol comes in and replaces the IP layer, leaving the other layers intact.  The only other manipulation required to get it working is access to the kernel's routing table, allowing us to route traffic in the right direction.

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

We're forced to specify a port to bind to by python's sockets, but we are able to share a port between multiple processes using `SO_REUSEPORT`, which is very cool.  This allows two clients to both receive packets sent to that port.  setblocking(0) is for convenience (just beware, you have to do some error handling to check if the socket is ready to read or write).

```python
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
s.setblocking(0)
s.bind(('',3003))

ready_to_read, ready_to_write, going_to_error_out = select.select([s], [s], [s], 1) # needed for nonblocking sockets
if s in ready_to_read:
   data = s.recvfrom(1024)

```

I've had the best success so far with libdnet (rather than scapy or pypcap).  dnet stands for "dumb networking", and that's exactly what it is.  It's a stupid-simple api to access raw sockets and network interfaces.  `dnet.iface('en1').send('HI')` will literally write "HI" to the network interface (with no ethernet frame, no IP header, to TCP header, just 'hi').  In fact, you can use this to DDoS individual people, or your entire local network.  Just run it in a `while True:` loop.  The stream of meaningless malformed packets caused the wifi connection at hackerschool to slow to a dead stop within seconds.  The full code for this style of attack can be found in `bring_it_down.py`.

Another issue I recently discovered is that most higher-end routers will cap broadcast UDP transmissions to their lowest possible transmit rate, to prevent flooding the LAN with traffic.  This is to encourage devs to use proper multicast so packets can be directed only to interested receiving parties, instead of sending every packet to every LAN receiver.  See this [Network Engineering Stack Exchange question] question](http://networkengineering.stackexchange.com/questions/1782/why-does-my-udp-broadcast-wireless-communication-is-capped-at-1mbs/) for more information about broadcast UDP transmit rate capping.


Cool Things:
------------
As I mentioned above, you can allow multiple processes to connect to the same socket on the same port, and they all recieve a duplicate of every packet sent to that socket.  This is a simple socket option, but the implications are great.  Now we can have multiple clients listen on the same port, meaning to the clients this is not longer a port, it's simply a broadcast interface.  Every client gets every packet.  Every client processes every packet, and filters out everything it doesn't care about.

```
datagram_socket = socket(AF_INET, SOCK_DGRAM)
datagram_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
```


Another cool thing is that you can create a virtual, virtual network interface that behaves like a real one in python.  The setup below allows us to write and recieve broadcast UDP packets to any interface.  In order to simulate our mesh networking protocol (which is at the IP layer, one level below UDP), we are going to simply cut off the IP, and UDP headers of every packet we recieve.  Since UDP allows us to do broadcast networking, we can simulate being at the ethernet level on the same hardware link as another computer by pretending we arent getting any help with routing from the system through IP and UDP.  We can then tack on our own routing protocol, I'm calling it "MESHP" for lack of a better name.  MESHP extends IPv6 and allows for mesh-style adhoc packet routing, but I'll save that for another time.  Below is the code for creating hard and virtual interfaces.

```python
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

```python
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

nodes[0].send("HELLO")

```

Each node accepts a list of links that it is connected to.  All the nodes on one link work like a broadcast ethernet.  You can visualize it as a bunch of serves connected to eachother using ethernet cables colored red, green, blue, and purple.  Except the red link is actually a real link, allowing you to test your nodes over wifi, bluetooth, or any other hardware interface.  Green, blue, and purple allow you to simulate branches of the network on your local computer in order to test topology.  The cool part about this is that it allows you to simulate a complex 350 node network using a couple of laptops connected with an ethernet cable or wifi.  To view the code for the class Node, check out `node.py`.

Links:
------

* http://dpk.io/blockchain
* http://www.aaronsw.com/weblog/squarezooko
* http://www.aaronsw.com/weblog/uncensor
* https://squaretriangle.jottit.com/faq
* http://libdnet.sourceforge.net/pydoc/public/frames.html
* https://github.com/SnabbCo/snabbswitch
* https://github.com/ewust
* https://en.wikipedia.org/wiki/IEEE_802.1aq (Shortest-Path-Bridging)
* https://developer.apple.com/reference/multipeerconnectivity (Apple's mesh framework)
* http://www.secdev.org/projects/scapy/
* http://battlemesh.org/ (Mesh Networking Battle conf)
