# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.5"

import sys
import random
import threading
import time
import select
from collections import defaultdict
from queue import Queue, Empty
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, SO_REUSEPORT

from protocols import SwitchProtocol, PrintProtocol, LoopbackFilter, StringFilter, DuplicateFilter

class BaseLink:
    broadcast_addr = "00:00:00:00:00:00:00"

    def __init__(self, name="vlan1"):
        self.name = name
        self.keep_listening = True
        self.inq = defaultdict(Queue)  # buffers for receiving packets
        # {'receiver_mac_address': Queue([packet1, packet2])}
        self.inq[self.broadcast_addr] = Queue()

    ### Utilities

    def __repr__(self):
        return "<"+self.name+">"

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        """number of mac addresses listening for packets on this link"""
        return len(self.inq)

    def log(self, *args):
        """stdout and stderr for the node"""
        print("%s %s" % (str(self).ljust(6), " ".join([str(x) for x in args])))

    ### Runloop

    def start(self):
        self.log("ready.")

    def stop(self):
        self.keep_listening = False
        # if threaded link, kill threads before going down
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
        self.log("sends packet to imaginary link...")

class VirtualLink(BaseLink):
    def send(self, packet):
        """place sent packets directly into the reciever's queues (as if they are connected by wire)"""
        if self.keep_listening:
            for addr, recv_queue in self.inq.items():
                recv_queue.put(packet)
        else:
            self.log("is down.")

class HardLink(threading.Thread, BaseLink):
    """
    for testing, all the nodes will connect to the hardware interface through this distributor
    otherwise, we run into issues with 5 (or 500) nodes all trying to read one packet from the same hardware iface
    """

    def __init__(self, name="en0", port=2016):
        # HardLinks have to be run in a seperate thread
        # they rely on the infinite run() loop to read packets out of the socket, which would block the main thread
        threading.Thread.__init__(self)
        BaseLink.__init__(self, name=name)
        self.__initsocket__(port=port)
        self.log("starting...")

    def __initsocket__(self, port=2016):
        self.port = port
        self.net_socket = socket(AF_INET, SOCK_DGRAM)
        self.net_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)  # requires sudo
        self.net_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.net_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.net_socket.setblocking(0)
        self.net_socket.bind(('', port))

    def __repr__(self):
        return "<"+self.name+">"

    ### Runloop

    def run(self):
        """runloop that reads incoming packets off the interface into the inq buffer"""
        self.log("real link established.")
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
                        # put the packet in that mac_addr recv queue
                        recv_queue.put(packet)
                else:
                    # packet got filtered due to UDP port mismatch between clients
                    pass
            time.sleep(0.01)

    ### IO

    def send(self, packet, retry=True):
        """send a packet down the line to the inteface"""
        addr = ('255.255.255.255', self.port)
        try:
            self.net_socket.sendto(packet, addr)
        except Exception as e:
            self.log("Link failed to send packet over socket %s" % e)
            time.sleep(0.2)
            if retry:
                self.send(packet, retry=False)

class Node(threading.Thread):
    def __init__(self, interfaces=None, name="n1", promiscuous=False, mac_addr=None, Filters=None, Protocol=PrintProtocol):
        threading.Thread.__init__(self)
        self.name = name
        self.interfaces = interfaces or []
        self.keep_listening = True
        self.promiscuous = promiscuous
        self.mac_addr = mac_addr or self.__genaddr__(6, 2)
        self.filters = Filters or [LoopbackFilter()]
        self.protocol = Protocol(node=self)

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
        self.join()

    ### Runloop

    def run(self):
        """networking loop init, this gets triggered by node.start()
        this runloop reads new packets off the link and feeds them to recv()
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
        """process a packet coming off the incoming packet buffer"""
        for f in self.filters:
            packet = f.tr(packet, interface)
        if packet:
            self.log("IN      ", str(interface).ljust(30), packet)
            self.protocol.recv(packet, interface)

    def send(self, packet, interfaces=None):
        """write packet to given interfaces, default is broadcast to all interfaces"""
        interfaces = interfaces or self.interfaces

        for interface in interfaces:
            for f in self.filters:
                packet = f.tx(packet, interface)
            if packet:
                self.log("OUT     ", ("<"+",".join(i.name for i in interfaces)+">").ljust(30), packet)
                interface.send(packet)

if __name__ == "__main__":
    interface = "en0"
    if len(sys.argv) > 1:
        interface = sys.argv[1]

    #         /-right-1-right2- \3
    # start <0                   end
    #         \--left-2-left2-- /4


    print("using a mix of real and vitual links to make a little network...")
    ls = (HardLink('en0', 2014), VirtualLink('vl1'), VirtualLink('vl2'), HardLink('en3', 2015), HardLink('en4', 2016))
    nodes = (
        Node([ls[0]], 'start'),
        Node([ls[0], ls[2]], 'l1', Protocol=SwitchProtocol),
        Node([ls[0], ls[1]], 'r1', Protocol=SwitchProtocol),
        Node([ls[2], ls[3]], 'l2', Filters=[LoopbackFilter(), DuplicateFilter()], Protocol=SwitchProtocol),
        Node([ls[1], ls[4]], 'r2', Filters=[LoopbackFilter(), StringFilter(b'red')], Protocol=SwitchProtocol),
        Node([ls[3], ls[4]], 'end'),
    )
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
