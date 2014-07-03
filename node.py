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
    port = 3003
    readface = None
    writeface = None

    def __init__(self, iface="en1", port=3003):
        self.name = iface
        self.port = port
        self.writeface = socket(AF_INET, SOCK_DGRAM)
        self.writeface.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.writeface.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.writeface.setblocking(0)

        self.readface = socket(AF_INET, SOCK_DGRAM)
        self.readface.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        self.readface.setblocking(0)
        self.readface.bind(('',port))

        print("[%s] up." % self.name)

    def send(self, indata):
        _1, ready_to_write, _2 = select.select([], [self.writeface], [], 1)     # needed for nonblocking sockets
        if self.writeface in ready_to_write and not self.writeface in _2:
            self.writeface.sendto(indata, ('255.255.255.255', self.port))
        else:
            print("NETWORK ERROR: WRITE FAILED")

    def recv(self):
        ready_to_read, _1, _2 = select.select([self.readface], [], [], 1)       # needed for nonblocking sockets
        if self.readface in ready_to_read and not self.readface in _2:
            try:
                return self.readface.recvfrom(1024)
            except Exception:
                return self.recv()                                               # just wait until it's available
        else:
            return ""

    def stop(self):
        # self.writeface = open('/dev/null', 'w') # not really necessary
        # self.readface = open('/dev/null', 'r') # not really necessary
        print("[%s] went down." % self.name)

class VirtualLink:
    name = "vlan"
    data = []
    port = ""

    def __init__(self, name="vlan"):
        self.name = name

    def send(self, indata):
        self.data.append(indata)

    def recv(self):
        if self.data:
            return self.data.pop()

    def stop(self):
        print("%s went down." % self.name)

class BaseProtocol:
    listeners = {}

    def broadcast(*args, **kwargs):
        pass
    def send(*args, **kwargs):
        pass
    def receive(*args, **kwargs):
        pass
    def ignore(*args, **kwargs):
        pass

    def add_listener(self, pattern, callback):
        """wait for packets matching a pattern, and feed them into their proper callback"""
        self.listeners[pattern] = callback

    def remove_listener(self, pattern):
        """stop monitoring for packets that match a given pattern"""
        self.listeners.pop(pattern)

class MeshProtocol(BaseProtocol):
    def __init__(self):
        self.listeners["syn"] = self.respond__hello
        self.listeners["SYN"] = self.respond__hello
        self.listeners["PAN"] = self.respond__hello
        self.listeners["KILL"] = self.stop
        self.listeners["kill"] = self.stop

    mesh_header = ";MESHPBEGIN;"            # beginnings of the MESHP protocol
    mesh_footer = ";MESHPEND;"

    def request__hello(self):
        self.broadcast("SYN")
        self.add_listener(pattern="ACK", callback=process_hello_response)

    def respond__hello(self, packet, *args):
        self.broadcast("ACK;")

class JSONMeshProtocol(BaseProtocol):
    def __init__():
        self.listeners["ACK"] = self.respond__hello
        self.listeners["HELLO"] = self.respond__hello
        self.listeners["PAN"] = self.respond__hello
        self.listeners["KILL"] = self.stop

    def request__hello(self):
        self.broadcast("SYN")
        self.add_listener(pattern="ACK", callback=process_hello_response)

    def respond__hello(self, packet):
        self.broadcast(";ACK %s;" % packet)

class Node(threading.Thread, MeshProtocol):
    interfaces = []
    keep_listening = True
    mac_addr = "10:9a:dd:4b:e9:eb"
    ip_addr = "eeee:::::::1"
    own_addr = "fasdfsdafsa"
    name = "node"

    def __init__(self, network_links, name=None):
        self.mac_addr = self.__genaddr__(6,2)
        self.ip_addr = self.__genaddr__(8,4)
        if name is None:
            self.name = self.mac_addr
        self.interfaces = network_links
        MeshProtocol.__init__(self)
        threading.Thread.__init__(self)

    def run(self):
        """networking loop init, this gets called on node.start()"""
        while self.keep_listening:
            for link in self.interfaces:
                packet = link.recv()
                if packet:
                    self.receive(packet)

    def stop(self):
        self.keep_listening = False
        print("\n[%s] went down." % self.name)

    @staticmethod
    def __genaddr__(len=6, sub_len=2):
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
        if self.own_addr not in packet:
            self.log("IN ", packet)
            for pattern, callback in self.listeners.iteritems():
                if pattern in packet:
                    try:
                        callback(packet)
                    except TypeError:
                        callback()

    def send(self, packet, links=interfaces):
        """write packet to an interface or several interfaces"""
        self.log("OUT", (packet, ("255.255.255.255", self.interfaces[0].port)))
        try:
            for interface in links:
                interface.send(packet)
        except TypeError:
            # fail gracefully if its only a single interface and not a list of interfaces
            links.push(packet)

    def broadcast(self, packet):
        """broadcast packet on all interfaces"""
        self.send(packet=packet, links=self.interfaces)

if __name__ == "__main__":
    link = HardLink("en1", 2020)
    node = Node([link])
    node.start()

    try:
        while True:
            message = raw_input()
            if message == "stop":
                raise KeyboardInterrupt
            else:
                node.broadcast(message)
            time.sleep(0.5)

    except KeyboardInterrupt:
        node.stop()
        link.stop()
        print("EXITING")
        exit(0)
