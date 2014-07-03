# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.1a"   

import random
import threading
import time
import select
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, SO_REUSEPORT
random.seed(None)   # defaults to system time

class HardLink:
    name = "en0"
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
            print("NETWORK ERROR: WRITE FAILED")

    def recv(self):
        ready_to_read, _1, _2 = select.select([self.readface], [], [], 1)       # needed for nonblocking sockets
        if ready_to_read:
            return self.readface.recvfrom(1024)
        else:
            return ""

class VirtualLink:
    name = "vlan"
    data = []

    def __init__(self, name="vlan"):
        self.name = name

    def send(self, indata):
        self.data.append(indata)

    def recv(self):
        if self.data:
            return self.data.pop()

class Node(threading.Thread):
    interfaces = []
    listeners = {}

    received = []
    sent = []

    _keep_listening = True

    mac_addr = "10:9a:dd:4b:e9:eb"
    ip_addr = "eeee:::::::1"

    mesh_header = "MESHP(1.0,IPV6);MESHP:BEGIN;"            # beginnings of the MESHP protocol
    mesh_footer = "MESHP:END;"

    def __init__(self, network_links):
        self.interfaces = network_links
        self.add_listener("SYN", self.respond__hello)
        threading.Thread.__init__(self)

    def run(self):
        """networking loop init, this gets called on node.start()"""
        while self._keep_listening:
            for link in self.interfaces:
                packet = link.recv()
                if packet:
                    self.receive(packet)

    @staticmethod
    def __genmacaddr__(len=6, sub_len=2):
        """generate a non-guaranteed-unique mac address"""
        addr = []
        for _ in range(len):
            sub = ""
            for _ in range(sub_len):
                sub += random.choice("0123456789abccef")
            addr.append(sub)
        return ":".join(addr)

    def log(self, *args):
        print("[%s] %s" % (self.name, " ".join([ str(x) for x in args])))

    def receive(self, packet):
        """receive and process data from an interface"""
        self.log("IN ", packet)
        for pattern, callback in self.listeners.iteritems():
            if pattern in packet:
                callback(self, packet)

    def send(self, packet, links=interfaces):
        """write packet to an interface or several interfaces"""
        self.log("OUT ", packet)
        try:
            for interface in links:
                interface.send(self.mesh_header+packet+self.mesh_footer)
        except TypeError:
            # fail gracefully if its only a single interface and not a list of interfaces
            links.push(self.mesh_header+packet+self.mesh_footer)

    def broadcast(self, packet):
        """broadcast packet on all interfaces"""
        self.send(packet=packet, links=self.interfaces)

    def add_listener(self, pattern, callback=log):
        """wait for packets matching a pattern, and feed them into their proper callback"""
        self.listeners[pattern] = callback

    def request__hello(self):
        self.broadcast("SYN")
        self.add_listener(pattern="ACK", callback=process_hello_response)

    def respond__hello(self, packet, *args):
        self.broadcast("ACK;")

if __name__ == "__main__":
    link = HardLink("en1")
    node = Node([link])
    node.start()

    while True:
        message = raw_input()
        node.broadcast(message)
        time.sleep(1)
