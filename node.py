# -*- coding: utf-8 -*-
# MIT License: Nick Sweeting

import random
import threading
import time
from collections import defaultdict
from queue import Queue

from links import VirtualLink, UDPLink, IRCLink
from programs import Switch, Printer
from filters import LoopbackFilter, DuplicateFilter, UniqueFilter, StringFilter

# Physical Layer (copper, fiber, audio, wireless)
# Link Layer (ethernet, ARP, PPP): links.py
# Network Layer (IPv4, IPv6, ICMP, MeshP): scapy
# Transport Layer (TCP, UDP, SCTP): scapy


# Nodes connect to each other over links.  The node has a runloop that pulls packets off the link's incoming packet Queue,
# runs them through its list of filters, then places it in the nodes incoming packet queue for that interface node.inq.
# the Node's Program is has a seperate runloop in a different thread that is constantly calling node.inq.get().
# The program does something with the packet (like print it to the screen, or reply with "ACK"), and sends any outgoing responses
# by calling the Node's send() method directly.  The Node runs the packet through it's outgoing packet filters in order, then
# if it wasn't dropped, calls the network interface's .send() method to push it over the network.

#  --> incoming packet queue | -> pulls packets off link's inq -> filters -> node.inq |  -> pulls packets off the node's inq
#              [LINK]        |                         [NODE]                         |               [PROGRAM]
#  <-- outgoing Link.send()  |   <----  outgoing filters  <-----  Node.send()  <----- |  <- sends responses by calling Node.send()

class Node(threading.Thread):
    """a Node represents a computer.  node.interfaces contains the list of network links the node is connected to.
        Nodes process incoming traffic through their filters, then place packets in their inq for their Program to handle.
        Programs process packets off the node's incoming queue, then send responses out through node's outbound filters,
        and finally out to the right network interface.
    """
    def __init__(self, interfaces=None, name="n1", promiscuous=False, mac_addr=None, Filters=(), Program=None):
        threading.Thread.__init__(self)
        self.name = name
        self.interfaces = interfaces or []
        self.keep_listening = True
        self.promiscuous = promiscuous
        self.mac_addr = mac_addr or self._generate_MAC(6, 2)
        self.inq = defaultdict(Queue)
        self.filters = [LoopbackFilter()] + [F() for F in Filters)]             # initialize the filters that shape incoming and outgoing traffic before it hits the program
        self.program = Program(node=self) if Program else None                  # init the program that will be processing incoming packets

    def __repr__(self):
        return "[{0}]".format(self.name)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def _generate_MAC(segments=6, segment_length=2, delimiter=":", charset="0123456789abcdef"):
        """generate a non-guaranteed-unique mac address"""
        addr = []
        for _ in range(segments):
            sub = ''.join(random.choice(charset) for _ in range(segment_length))
            addr.append(sub)
        return delimiter.join(addr)

    def log(self, *args):
        """stdout and stderr for the node"""
        print("%s %s" % (str(self).ljust(8), " ".join(str(x) for x in args)))

    def stop(self):
        self.keep_listening = False
        if self.program: self.program.stop()
        self.join()
        return True

    ### Runloop

    def run(self):
        """runloop that gets triggered by node.start()
        reads new packets off the link and feeds them to recv()
        """
        if self.program:
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
            if not packet:
                break
            packet = f.tr(packet, interface)
        if packet:
            # if the packet wasn't dropped by a filter, log the recv and place it in the interface's inq
            # self.log("IN      ", str(interface).ljust(30), packet.decode())
            self.inq[interface].put(packet)

    def send(self, packet, interfaces=None):
        """write packet to given interfaces, default is broadcast to all interfaces"""
        interfaces = interfaces or self.interfaces  # default to all interfaces
        interfaces = interfaces if hasattr(interfaces, '__iter__') else [interfaces]

        for interface in interfaces:
            for f in self.filters:
                packet = f.tx(packet, interface)  # run outgoing packet through the filters
            if packet:
                # if not dropped, log the transmit and pass it to the interface's send method
                # self.log("OUT     ", ("<"+",".join(i.name for i in interfaces)+">").ljust(30), packet.decode())
                interface.send(packet)

if __name__ == "__main__":
    print("Using a mix of real and vitual links to make a little network...\n")
    print("          /[r1]<--vlan1-->[r2]<----vlan4---\\")
    print("[start]-en0                                [end]")
    print("          \[l1]<--vlan2-->[l2]<--irc3:irc5-/\n")

    # ls = (UDPLink('en0', 2014), VirtualLink('vl1'), VirtualLink('vl2'), IRCLink('irc3'), UDPLink('en4', 2016), IRCLink('irc5'))          # slow, but impressive to connect over IRC
    ls = (UDPLink('en0', 2010), VirtualLink('vl1'), VirtualLink('vl2'), UDPLink('irc3', 2013), UDPLink('en4', 2014), UDPLink('irc5', 2013))    # faster setup for quick testing
    nodes = (
        Node([ls[0]], 'start'),
        Node([ls[0], ls[2]], 'l1', Program=Switch),
        Node([ls[0], ls[1]], 'r1', Program=Switch),
        Node([ls[2], ls[3]], 'l2', Filters=(DuplicateFilter,), Program=Switch),              # l2 wont forward two of the same packet in a row
        Node([ls[1], ls[4]], 'r2', Filters=(StringFilter.match(b'red'),), Program=Switch),   # r2 wont forward any packet unless it contains the string 'red'
        Node([ls[4], ls[5]], 'end', Program=Printer),
    )
    [l.start() for l in ls]
    [n.start() for n in nodes]

    print('\n', nodes)
    print("l2 wont forward two of the same packet in a row.")
    print("r2 wont forward any packet unless it contains the string 'red'.")
    print("Experiment by typing packets for [start] to send out, and seeing if they make it to the [end] node.")

    try:
        while True:
            print("------------------------------")
            message = input("[start]  OUT:".ljust(49))
            nodes[0].send(bytes(message, 'UTF-8'))
            time.sleep(1)

    except (EOFError, KeyboardInterrupt):   # CTRL-D, CTRL-C
        print(("All" if all([n.stop() for n in nodes]) else 'Not all') + " nodes stopped cleanly.")
        print(("All" if all([l.stop() for l in ls]) else 'Not all')    + " links stopped cleanly.")
