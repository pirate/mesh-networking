# -*- coding: utf-8 -*-
# MIT Liscence: Nick Sweeting
version = "1.0"

import sys
import random
import threading
import time
import select
from collections import defaultdict
from queue import Queue, Empty
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, SO_REUSEPORT

from protocols import SwitchProtocol, PrintProtocol, LoopbackFilter, DuplicateFilter, StringFilter

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

        # buffer dict for receiving incoming packets
        # {'connectednode1': Queue([packet1, packet2])}
        self.inq = defaultdict(Queue)
        self.inq[self.broadcast_addr] = Queue()

    ### Utilities

    def __repr__(self):
        return "<"+self.name+">"

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        """number of nodes listening for packets on this link"""
        return len(self.inq)

    def log(self, *args):
        """stdout and stderr for the link"""
        print("%s %s" % (str(self).ljust(6), " ".join([str(x) for x in args])))

    ### Runloop

    def start(self):
        """all links need to have a start() method because threaded ones use it start their runloops"""
        self.log("ready.")

    def stop(self):
        """all links also need stop() to stop their runloops"""
        self.keep_listening = False
        # if threaded, kill threads before going down
        if hasattr(self, 'join'):
            self.join()
        self.log("went down.")

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

    def send(self, packet):
        """place sent packets directly into the reciever's queues (as if they are connected by wire)"""
        if self.keep_listening:
            for addr, recv_queue in self.inq.items():
                recv_queue.put(packet)
        else:
            self.log("is down.")

class HardLink(threading.Thread, VirtualLink):
    """This link sends all traffic as BROADCAST UDP packets on all physical ifaces.
    Connect nodes on two different laptops to a HardLink() with the same port and they will talk over wifi or ethernet.
    """

    def __init__(self, name="en0", port=2016):
        # HardLinks have to be run in a seperate thread
        # they rely on the infinite run() loop to read packets out of the socket, which would block the main thread
        threading.Thread.__init__(self)
        VirtualLink.__init__(self, name=name)
        self.port = port
        self.log("starting...")
        self.__initsocket__()

    def __repr__(self):
        return "<"+self.name+">"

    def __initsocket__(self):
        """bind to the datagram socket (UDP), and enable BROADCAST mode"""
        self.net_socket = socket(AF_INET, SOCK_DGRAM)
        self.net_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)  # requires sudo
        self.net_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # allows multiple HardLinks to all listen for UDP packets
        self.net_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.net_socket.setblocking(0)
        self.net_socket.bind(('', self.port))

    ### Runloop

    def run(self):
        """runloop that reads incoming packets off the interface into the inq buffer"""
        self.log("ready to receive.")
        # we use a runloop instead of synchronous recv so stopping the node mid-recv is possible
        while self.keep_listening:
            try:
                read_ready, w, x = select.select([self.net_socket], [], [], 0.2)
            except Exception:
                # catch timeouts
                r = []
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
            self.net_socket.sendto(packet, addr)
        except Exception as e:
            self.log("Link failed to send packet over socket %s" % e)
            time.sleep(0.2)
            if retry:
                self.send(packet, retry=False)

class IRCLink(threading.Thread, VirtualLink):
    """This link connects to an IRC channel and uses it to simulate a BROADCAST link.
    Connect nodes on different computers to an IRCLink on the same channel and they will talk over the internet."""
    def __init__(self, name='irc1', server='irc.freenode.net', port=6667, channel='##medusa', nick='bobbyTables'):
        threading.Thread.__init__(self)
        VirtualLink.__init__(self, name=name)
        self.name = name
        self.server = server
        self.port = port
        self.channel = channel
        self.nick = nick if nick != 'bobbyTables' else 'bobbyTables'+str(random.randint(1, 1000))
        self.log("starting...")
        self.__connect__()
        self.__joinchannel__()
        self.log("irc channel connected.")

    def __repr__(self):
        return "<"+self.name+">"

    def stop(self):
        self.net_socket.send(b"QUIT\r\n")
        VirtualLink.stop(self)

    def __parse__(self, msg):
        if b"PRIVMSG" in msg:
            from_nick = msg.split(b"PRIVMSG ",1)[0].split(b"!")[0][1:]              # who sent the PRIVMSG
            to_nick = msg.split(b"PRIVMSG ",1)[1].split(b" :",1)[0]                 # where did they send it
            text = msg.split(b"PRIVMSG ",1)[1].split(b" :",1)[1].strip()            # what did it contain
            return (text, from_nick)
        elif msg.find(b"PING :",0,6) != -1:                                         # was it just a ping?
            from_srv = msg.split(b"PING :")[1].strip()                              # the source of the PING
            return ("PING", from_srv)
        return ("","")

    def __connect__(self):
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
            except:
                msg = None

    def __joinchannel__(self):
        self.log("joining channel %s as %s..." % (self.channel, self.nick))
        nick = self.nick
        self.net_socket.settimeout(10)
        self.net_socket.send(('NICK %s\r\n' % nick).encode('utf-8'))
        self.net_socket.send(('USER %s %s %s :%s\r\n' % (nick, nick, nick, nick)).encode('utf-8'))
        self.net_socket.send(('JOIN %s\r\n' % self.channel).encode('utf-8'))
        msg = self.net_socket.recv(4096)
        while msg:
            if b"Nickname is already in use" in msg:
                self.nick += str(random.randint(1, 1000))
                self.__joinchannel__()
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
        self.net_socket.settimeout(0.2)
        while self.keep_listening:
            try:
                packet = self.net_socket.recv(4096)
            except:
                packet = None
            if packet:
                packet, source = self.__parse__(packet)
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
        if self.keep_listening:
            try:
                # (because the IRC server sees this link as 1 connection no matter how many nodes use it, it wont send enough copies of the packet back)
                # for each node listening to this link object locally
                for mac_addr, recv_queue in self.inq.items():
                    recv_queue.put(packet) # put the packet directly in their in queue
                # then send it down the wire to the IRC channel
                self.net_socket.send(('PRIVMSG %s :%s\r\n' % (self.channel, packet.decode())).encode('utf-8'))
            except Exception as e:
                self.log("Link failed to send packet over socket %s" % e)
                time.sleep(0.2)
                if retry:
                    self.send(packet, retry=False)
        else:
            self.log('is down.')

class Node(threading.Thread):
    def __init__(self, interfaces=None, name="n1", promiscuous=False, mac_addr=None, Filters=(LoopbackFilter,), Protocol=PrintProtocol):
        threading.Thread.__init__(self)
        self.name = name
        self.interfaces = interfaces or []
        self.keep_listening = True
        self.promiscuous = promiscuous
        self.mac_addr = mac_addr or self.__genaddr__(6, 2)
        self.inq = defaultdict(Queue)
        self.filters = [F() for F in Filters]  # initialize the filters that shape incoming and outgoing traffic before it hits the Protocol
        self.protocol = Protocol(node=self)    # init and start the Protocol (program that will be processing incoming packets)
        self.protocol.start()

    def __repr__(self):
        return "["+self.name+"]"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def __genaddr__(len=6, sub_len=2):
        """generate a non-guaranteed-unique mac address"""
        addr = []
        for _ in range(len):
            sub = ''.join(random.choice("0123456789abcdef") for _ in range(sub_len))
            addr.append(sub)
        return ":".join(addr)

    def log(self, *args):
        """stdout and stderr for the node"""
        print("%s %s" % (str(self).ljust(6), " ".join([str(x) for x in args])))

    def stop(self):
        self.keep_listening = False
        self.protocol.stop()
        self.join()

    ### Runloop

    def run(self):
        """runloop that gets triggered by node.start()
        reads new packets off the link and feeds them to recv()
        """
        while self.keep_listening:
            for interface in self.interfaces:
                packet = interface.recv(self.mac_addr if not self.promiscuous else "00:00:00:00:00:00")
                if packet:
                    self.recv(packet, interface)
                time.sleep(0.01)
        self.log("Stopped listening.")

    ### IO
        
    def recv(self, packet, interface):
        """run incoming packet through the filters, then place it in its inq"""
        # the packet is piped into the first filter, then the result of that into the second, etc.
        for f in self.filters:
            packet = f.tr(packet, interface)
        if packet:
            # if the packet wasn't dropped by a filter, log the recv and place it in the interface's inq
            self.log("IN      ", str(interface).ljust(30), packet)
            self.inq[interface].put(packet)

    def send(self, packet, interfaces=None):
        """write packet to given interfaces, default is broadcast to all interfaces"""
        interfaces = interfaces or self.interfaces  # default to all interfaces

        for interface in interfaces:
            for f in self.filters:
                packet = f.tx(packet, interface)  # run outgoing packet through the filters
            if packet:
                # if not dropped, log the transmit and pass it to the interface's send method
                self.log("OUT     ", ("<"+",".join(i.name for i in interfaces)+">").ljust(30), packet)
                interface.send(packet)

if __name__ == "__main__":
    print("Using a mix of real and vitual links to make a little network...")
    print(r""" /[r1]<--vlan1-->[r2]<---vlan4---\
    [start]-en0                                [end]
               \[l1]<--vlan2-->[l2]<-irc3:irc5-/""")

    ls = (HardLink('en0', 2014), VirtualLink('vl1'), VirtualLink('vl2'), IRCLink('irc3'), HardLink('en4', 2016), IRCLink('irc5'))
    nodes = (
        Node([ls[0]], 'start'),
        Node([ls[0], ls[2]], 'l1', Protocol=SwitchProtocol),
        Node([ls[0], ls[1]], 'r1', Protocol=SwitchProtocol),
        Node([ls[2], ls[3]], 'l2', Filters=[LoopbackFilter, DuplicateFilter], Protocol=SwitchProtocol),
        Node([ls[1], ls[4]], 'r2', Filters=[LoopbackFilter, StringFilter.match(b'red')], Protocol=SwitchProtocol),
        Node([ls[5], ls[4]], 'end'),            # l2 wont forward two of the same packet in a row
    )                                           # r2 wont forward any packet unless it contains the string 'red'
    [l.start() for l in ls]
    [n.start() for n in nodes]
    
    try:
        while True:
            print("------------------------------")
            message = input("[start] OUT:".ljust(49))
            nodes[0].send(bytes(message, 'UTF-8'))
            time.sleep(0.5)

    except (EOFError, KeyboardInterrupt):
        [n.stop() for n in nodes]
        [l.stop() for l in ls]
        print("EXITING")
        exit(0)
