# -*- coding: utf-8 -*-
# MIT License: Nick Sweeting
__version__ = "1.0"

import random
import threading
import time
from collections import defaultdict
from queue import Queue

from links import VirtualLink, UDPLink, IRCLink
from programs import Switch, Printer
from filters import LoopbackFilter, DuplicateFilter, UniqueFilter, StringFilter

class Node(threading.Thread):
    """a Node represents a computer.  node.interfaces is a list of the network links it's connected to.
        Nodes process incoming traffic through it's filters, then places it in its inq for its Program to handle.
        Programs process packets off the node's incoming queue, then send responses out the node's outbound filters, 
        and finally out to the right network interface.
    """
    def __init__(self, interfaces=None, name="n1", promiscuous=False, mac_addr=None, Filters=None, Program=Printer):
        threading.Thread.__init__(self)
        self.name = name
        self.interfaces = interfaces or []
        self.keep_listening = True
        self.promiscuous = promiscuous
        self.mac_addr = mac_addr or self.__genaddr__(6, 2)
        self.inq = defaultdict(Queue)
        self.filters = [LoopbackFilter(), UniqueFilter()] + [F() for F in (Filters or [])] # initialize the filters that shape incoming and outgoing traffic before it hits the program
        self.program = Program(node=self)    # init and start the program (program that will be processing incoming packets)

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
        print("%s %s" % (str(self).ljust(8), " ".join([str(x) for x in args])))

    def stop(self):
        self.keep_listening = False
        self.program.stop()
        self.join()

    ### Runloop

    def run(self):
        """runloop that gets triggered by node.start()
        reads new packets off the link and feeds them to recv()
        """
        self.program.start()
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
        # the packet is piped into the first filter, then the result of that into the second filter, etc.
        for f in self.filters:
            packet = f.tr(packet, interface)
        if packet:
            # if the packet wasn't dropped by a filter, log the recv and place it in the interface's inq
            self.log("IN      ", str(interface).ljust(30), packet.decode())
            self.inq[interface].put(packet)

    def send(self, packet, interfaces=None):
        """write packet to given interfaces, default is broadcast to all interfaces"""
        interfaces = interfaces or self.interfaces  # default to all interfaces

        for interface in interfaces:
            for f in self.filters:
                packet = f.tx(packet, interface)  # run outgoing packet through the filters
            if packet:
                # if not dropped, log the transmit and pass it to the interface's send method
                self.log("OUT     ", ("<"+",".join(i.name for i in interfaces)+">").ljust(30), packet.decode())
                interface.send(packet)

if __name__ == "__main__":
    print("Using a mix of real and vitual links to make a little network...\n")
    print("          /[r1]<--vlan1-->[r2]<----vlan4---\\")
    print("[start]-en0                                [end]")
    print("          \[l1]<--vlan2-->[l2]<--irc3:irc5-/\n")

    # ls = (UDPLink('en0', 2014), VirtualLink('vl1'), VirtualLink('vl2'), IRCLink('irc3'), UDPLink('en4', 2016), IRCLink('irc5'))
    ls = (UDPLink('en0', 2014), VirtualLink('vl1'), VirtualLink('vl2'), VirtualLink('irc3'), UDPLink('en4', 2016), VirtualLink('irc5'))
    nodes = (
        Node([ls[0]], 'start'),
        Node([ls[0], ls[2]], 'l1', Program=Switch),
        Node([ls[0], ls[1]], 'r1', Program=Switch),
        Node([ls[2], ls[3]], 'l2', Filters=[LoopbackFilter, DuplicateFilter], Program=Switch),
        Node([ls[1], ls[4]], 'r2', Filters=[LoopbackFilter, StringFilter.match(b'red')], Program=Switch),
        Node([ls[5], ls[4]], 'end'),            # l2 wont forward two of the same packet in a row
    )                                           # r2 wont forward any packet unless it contains the string 'red'
    [l.start() for l in ls]
    [n.start() for n in nodes]
    
    try:
        while True:
            print("------------------------------")
            message = input("[start]  OUT:".ljust(49))
            nodes[0].send(bytes(message, 'UTF-8'))
            time.sleep(0.5)

    except (EOFError, KeyboardInterrupt):
        [n.stop() for n in nodes]
        [l.stop() for l in ls]
        print("EXITING")
        exit(0)
