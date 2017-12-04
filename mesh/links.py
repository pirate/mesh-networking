import threading

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

from time import sleep
from random import randint
from collections import defaultdict

import select
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST

try:
    # needed for BSD systems like macOS
    from socket import SO_REUSEPORT
    IS_BSD = True
except:
    # not needed on non-BSD systems (e.g. linux)
    IS_BSD = False


class VirtualLink:
    """A Link represents a network link between Nodes.
    Nodes.interfaces is a list of the [Link]s that it's connected to.
    Some links are BROADCAST (all connected nodes get a copy of all packets),
    others are UNICAST (you only see packets directed to you), or
    MULTICAST (you can send packets to several people at once).
    Some links are virtual, others actually send the traffic over UDP or IRC.
    Give two nodes the same VirtualLink() object to simulate connecting them with a cable."""
    broadcast_addr = "00:00:00:00:00:00:00"

    def __init__(self, name="vlan1"):
        self.name = name
        self.keep_listening = True

        # buffer for receiving incoming packets
        self.inq = defaultdict(Queue)  # mac_addr: [packet1, packet2, ...]
        self.inq[self.broadcast_addr] = Queue()

    ### Utilities

    def __repr__(self):
        return "<%s>" % self.name

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        """number of nodes listening for packets on this link"""
        return len(self.inq)

    def log(self, *args):
        """stdout and stderr for the link"""
        print("%s %s" % (str(self).ljust(8), " ".join([str(x) for x in args])))

    ### Runloop

    def start(self):
        """all links need to have a start() method because threaded ones use it start their runloops"""
        self.log("ready.")
        return True

    def stop(self):
        """all links also need stop() to stop their runloops"""
        self.keep_listening = False
        # if threaded, kill threads before going down
        if hasattr(self, 'join'):
            self.join()
        self.log("Went down.")
        return True

    ### IO

    def recv(self, mac_addr=broadcast_addr, timeout=0):
        """read packet off the recv queue for a given address, optional timeout to block and wait for packet"""
        # recv on the broadcast address "00:..:00" will give you all packets (for promiscuous mode)
        if self.keep_listening:
            try:
                return self.inq[str(mac_addr)].get(timeout=timeout)
            except Empty:
                return ""
        else:
            self.log("is down.")

    def send(self, packet, mac_addr=broadcast_addr):
        """place sent packets directly into the reciever's queues (as if they are connected by wire)"""
        if self.keep_listening:
            if mac_addr == self.broadcast_addr:
                for addr, recv_queue in self.inq.items():
                    recv_queue.put(packet)
            else:
                self.inq[mac_addr].put(packet)
                self.inq[self.broadcast_addr].put(packet)
        else:
            self.log("is down.")

class UDPLink(threading.Thread, VirtualLink):
    """This link sends all traffic as BROADCAST UDP packets on all physical ifaces.
    Connect nodes on two different laptops to a UDPLink() with the same port and they will talk over wifi or ethernet.
    """

    def __init__(self, name="en0", port=2016):
        # UDPLinks have to be run in a seperate thread
        # they rely on the infinite run() loop to read packets out of the socket, which would block the main thread
        threading.Thread.__init__(self)
        VirtualLink.__init__(self, name=name)
        self.port = port
        # self.log("starting...")
        self._initsocket()

    def __repr__(self):
        return "<" + self.name + ">"

    def _initsocket(self):
        """bind to the datagram socket (UDP), and enable BROADCAST mode"""
        self.send_socket = socket(AF_INET, SOCK_DGRAM)
        self.send_socket.setblocking(0)
        self.send_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        self.recv_socket = socket(AF_INET, SOCK_DGRAM)
        self.recv_socket.setblocking(0)
        if IS_BSD:
            self.recv_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)  # requires sudo
        self.recv_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # allows multiple UDPLinks to all listen for UDP packets
        self.recv_socket.bind(('', self.port))

    ### Runloop

    def run(self):
        """runloop that reads incoming packets off the interface into the inq buffer"""
        # self.log("ready to receive.")
        # we use a runloop instead of synchronous recv so stopping the node mid-recv is possible
        read_ready = None

        while self.keep_listening:
            try:
                read_ready, w, x = select.select([self.recv_socket], [], [], 0.01)
            except Exception:
                # catch timeouts
                pass

            if read_ready:
                packet, addr = read_ready[0].recvfrom(4096)
                if addr[1] == self.port:
                    # for each address listening to this link
                    for mac_addr, recv_queue in self.inq.items():
                        recv_queue.put(packet)  # put packet in node's recv queue
                else:
                    pass  # not meant for us, it was sent to a different port

    ### IO

    def send(self, packet, retry=True):
        """send a packet down the line to the inteface"""
        addr = ('255.255.255.255', self.port)  # 255. is the broadcast IP for UDP
        try:
            self.send_socket.sendto(packet, addr)
        except Exception as e:
            self.log("Link failed to send packet over socket %s" % e)
            sleep(0.2)
            if retry:
                self.send(packet, retry=False)

class IRCLink(threading.Thread, VirtualLink):
    """This link connects to an IRC channel and uses it to simulate a BROADCAST connection over the internet.
    Connect nodes on different computers to an IRCLink on the same channel and they will talk over the internet."""
    def __init__(self, name='irc1', server='irc.freenode.net', port=6667, channel='##medusa', nick='bobbyTables'):
        threading.Thread.__init__(self)
        VirtualLink.__init__(self, name=name)
        self.name = name
        self.server = server
        self.port = port
        self.channel = channel
        self.nick = nick if nick != 'bobbyTables' else 'bobbyTables' + str(randint(1, 1000))
        self.log("starting...")
        self._connect()
        self._join_channel()
        self.log("irc channel connected.")

    def __repr__(self):
        return "<"+self.name+">"

    def stop(self):
        self.net_socket.send(b"QUIT\r\n")
        VirtualLink.stop(self)

    def _parse_msg(self, msg):
        if b"PRIVMSG" in msg:
            from_nick = msg.split(b"PRIVMSG ",1)[0].split(b"!")[0][1:]              # who sent the PRIVMSG
            to_nick = msg.split(b"PRIVMSG ",1)[1].split(b" :",1)[0]                 # where did they send it
            text = msg.split(b"PRIVMSG ",1)[1].split(b" :",1)[1].strip()            # what did it contain
            return (text, from_nick)
        elif msg.find(b"PING :",0,6) != -1:                                         # was it just a ping?
            from_srv = msg.split(b"PING :")[1].strip()                              # the source of the PING
            return ("PING", from_srv)
        return ("","")

    def _connect(self):
        self.log("connecting to server %s:%s..." % (self.server, self.port))
        self.net_socket = socket(AF_INET, SOCK_STREAM)
        self.net_socket.connect((self.server, self.port))
        self.net_socket.setblocking(1)
        self.net_socket.settimeout(2)
        msg = self.net_socket.recv(4096)
        while msg:
            try:
                # keep reading 2 sec until servers stops sending text
                msg = self.net_socket.recv(4096).strip()
            except Exception:
                msg = None

    def _join_channel(self):
        self.log("joining channel %s as %s..." % (self.channel, self.nick))
        nick = self.nick
        self.net_socket.settimeout(10)
        self.net_socket.send(('NICK %s\r\n' % nick).encode('utf-8'))
        self.net_socket.send(('USER %s %s %s :%s\r\n' % (nick, nick, nick, nick)).encode('utf-8'))
        self.net_socket.send(('JOIN %s\r\n' % self.channel).encode('utf-8'))
        msg = self.net_socket.recv(4096)
        while msg:
            if b"Nickname is already in use" in msg:
                self.nick += str(randint(1, 1000))
                self._join_channel()
                return
            elif b"JOIN" in msg:
                # keep looping till we see JOIN, then we're succesfully in the room
                break
            try:
                msg = self.net_socket.recv(4096).strip()
            except:
                msg = None

    ### Runloop

    def run(self):
        """runloop that reads incoming packets off the interface into the inq buffer"""
        self.log("ready to receive.")
        # we use a runloop instead of synchronous recv so stopping the connection mid-recv is possible
        self.net_socket.settimeout(0.05)
        while self.keep_listening:
            try:
                packet = self.net_socket.recv(4096)
            except:
                packet = None
            if packet:
                packet, source = self._parse_msg(packet)
                if packet == "PING":
                    self.net_socket.send(b'PONG ' + source + b'\r')
                elif packet:
                    for mac_addr, recv_queue in self.inq.items():
                        # put the packet in that mac_addr recv queue
                        recv_queue.put(packet)
        self.log('is down.')

    ### IO

    def send(self, packet, retry=True):
        """send a packet down the line to the inteface"""
        if not self.keep_listening:
            self.log('is down.')
            return

        try:
            # (because the IRC server sees this link as 1 connection no matter how many nodes use it, it wont send enough copies of the packet back)
            # for each node listening to this link object locally
            for mac_addr, recv_queue in self.inq.items():
                recv_queue.put(packet) # put the packet directly in their in queue
            # then send it down the wire to the IRC channel
            self.net_socket.send(('PRIVMSG %s :%s\r\n' % (self.channel, packet.decode())).encode('utf-8'))
        except Exception as e:
            self.log("Link failed to send packet over socket %s" % e)
            sleep(0.2)
            if retry:
                self.send(packet, retry=False)

class RawSocketLink(threading.Thread, VirtualLink):
    """This link uses tun/tap interfaces to send and receive packets directly at the ethernet level"""

    def __init__(self):
        raise NotImplementedError()


class MultiPeerConnectivityLink(threading.Thread, VirtualLink):
    """This link sends traffic over Bluetooth to Apple devices using the MultiPeerConnectivity framework introduced in iOS 7.
    """

    def __init__(self):
        raise NotImplementedError()
