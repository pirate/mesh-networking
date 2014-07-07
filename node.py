# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.1a"   

import random
import threading
import time
import select
from Queue import Queue, Empty
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, SO_REUSEPORT
random.seed(None)   # defaults to system time

class VirtualLink(Queue):
    """
    The minimum requirement for a network interface (or link as it's referred to in this python program)

    Thins to keep in mind:
        - the link should have no knowledge of who is connected to it
        - the link transmits everything to everyone, broadcast style
            think of this as a group of computers conntected to eachother with wifi
            the only way to transmit messages is to braodcast them to everyone and have
            the receiving party filter out packets intended for other people.  In this
            implementation, a link is simply an abstaction for a pipe that allows nodes
            to communicate with eachother.  Two notes can share a single link, and then
            it acts as a simple two-way connection
    """
    name = ""
    nodes = []
    keep_listening = True

    def __init__(self, name="vlan", nodes=None):
        Queue.__init__(self)
        if not nodes is None:
            self.nodes = nodes
        self.name = name

    def __repr__(self):
        return "<"+self.name+">"

    def register(self, node):
        if not node in self.nodes:
            self.nodes.append(node)

    def deregister(self, node):
        if node in self.nodes:
            self.nodes.remove(node)

    def send(self, data):
        if self.keep_listening:
            self.put(data)

class HardLink(threading.Thread):
    port = 3003
    readface = None
    writeface = None
    name = ""
    nodes = ""
    keep_listening = True

    def __init__(self, iface="en1", port=3003, nodes=None):
        threading.Thread.__init__(self)
        self.port = port
        self.writeface = socket(AF_INET, SOCK_DGRAM)
        self.writeface.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.writeface.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        #self.writeface.setblocking(0)

        self.readface = socket(AF_INET, SOCK_DGRAM)
        self.readface.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        #self.readface.setblocking(1)
        self.readface.bind(('', int(self.port)))
        
        print("[%s] up." % self.name)

    def send(self, indata):
        self.writeface.sendto(indata, ('255.255.255.255', self.port))

    def run(self):
        while self.keep_listening:
            data = self.readface.recvfrom(1024)
            self.distribute(data)
        self.readface.close()
        self.writeface.close()

    def stop(self):
        self.keep_listening = False
        # self.writeface = open('/dev/null', 'w') # not really necessary
        # self.readface = open('/dev/null', 'r') # not really necessary
        print("[%s] went down." % self.name)

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
        self.broadcast("ACK")

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

    def __init__(self, network_links=None, name=None):
        MeshProtocol.__init__(self)
        threading.Thread.__init__(self)
        self.mac_addr = self.__genaddr__(6,2)
        self.ip_addr = self.__genaddr__(8,4)
        self.interfaces = network_links if not network_links is None else []
        if name is None:
            self.setName(self.mac_addr)
        else:
            self.setName(name)

    def __repr__(self):
        return "["+self.name+"]"

    def run(self):
        """networking loop init, this gets called on node.start()"""
        self.incoming = Queue()
        while self.keep_listening:
            for iface in self.interfaces:
                try:
                    self.parse(iface.get(timeout=0))
                    iface.task_done()
                except Empty:
                    pass

    def stop(self):
        self.keep_listening = False
        for interface in self.interfaces:
            interface.deregister(self)
        self.interfaces = []
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

    def add_interface(self, interface):
        self.interfaces += [interface]
        interface.register(self)

    def log(self, *args):
        """stdout and stderr for the node"""
        print("%s %s" % (self, " ".join([ str(x) for x in args])))

    def receive(self, packet):
        """receive and process data from an interface"""
        self.incoming.put(packet)
        
    def parse(self, packet):
        self.log("IN ", packet)
        if self.own_addr not in packet:
            for pattern, callback in self.listeners.iteritems():
                if pattern in packet:
                    try:
                        callback(packet)
                    except TypeError:
                        callback()

    def send(self, packet, links=interfaces):
        """write packet to an interface or several interfaces"""
        self.log("OUT", (packet, ("255.255.255.255", ",".join([ i.name for i in self.interfaces ]))))
        try:
            for interface in links:
                interface.send(packet)
        except TypeError:
            # fail gracefully if its only a single interface and not a list of interfaces
            links.send(packet)

    def broadcast(self, packet):
        """broadcast packet on all interfaces"""
        self.send(packet=packet, links=self.interfaces)

if __name__ == "__main__":
    link = HardLink("en1", 3002)
    link2 = VirtualLink("vlan1")
    node = Node([link, link2])
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
        node.join()
        link.join()
        print("EXITING")
        exit(0)


# [c9:f6:24:4b:1e:6e] IN  ('{"id":"1f5ff4bc2416cf63f03bdb14242710be63da84c4","origin_peer":{"id":"B","address":"10.0.5.33:3003","connected_peers":[{"id":"A","address":"10.0.5.33:3001"},{"id":"C","address":"10.0.5.33:7666","connected_peers":[{"id":"D","address":"10.0.5.33:1111"}]}]},"destination_id":""}', ('10.0.5.33', 53934))
