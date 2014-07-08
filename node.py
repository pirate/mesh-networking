# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.1a"   

import random
import threading
import time
import select
from Queue import Queue, Empty
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, SO_REUSEPORT, SOCK_RAW, IPPROTO_UDP, error
random.seed(None)   # defaults to system time

class VirtualLink():
    name = ""
    keep_listening = True
    inq = {}

    def __repr__(self):
        return "<"+self.name+">"

    def __init__(self, iface="vlan", port=None):
        self.name = iface

    def register(self, node_mac_addr):
        self.inq[str(node_mac_addr)] = Queue()

    def deregister(self, node_mac_addr):
        self.inq.pop(str(node_mac_addr))

    def recv(self, node_mac_addr):
        if self.keep_listening:
            try:
                return self.inq[str(node_mac_addr)].get(timeout=0)
            except Empty:
                return ""

    def send(self, data):
        if self.keep_listening:
            for addr, nodeq in inq.iteritems():
                nodeq.put(data)

    def stop(self):
        self.keep_listening = False
        print("[%s] went down." % self.name)


class HardLink(threading.Thread):
    """
    for testing, all the nodes will connect to the hardware interface through this distributor
    otherwise, we run into issues with 5 (or 500) nodes all trying to read one packet from the same hardware iface
    """

    port = 3003
    interface = None
    name = ""
    keep_listening = True
    inq = {}

    def __repr__(self):
        return "<"+self.name+">"

    def __init__(self, iface="en1", port=3003):
        threading.Thread.__init__(self)
        self.port = port
        self.name = iface+":"+str(port)

        self.interface = socket(AF_INET, SOCK_DGRAM)
        self.interface.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        self.interface.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.interface.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.interface.setblocking(0)
        self.interface.bind(('',port))

        print("[%s] up." % self.name)

    def register(self, node_mac_addr):
        self.inq[node_mac_addr] = Queue()

    def deregister(self, node_mac_addr):
        self.inq.pop(node_mac_addr)

    def run(self):
        while self.keep_listening:
            try:
                r, w, x = select.select([self.interface], [], [], 0.2)
            except Exception:
                # catch timeouts
                r = []
            for i in r:
                data, addr = i.recvfrom(4096)
                print addr[1], self.port
                if addr[1] == self.port:
                    for _, nodeq in self.inq.iteritems():
                        nodeq.put((data, addr))
                else:
                    print "filtered"

    def recv(self, node_mac_addr):
        if self.keep_listening:
            try:
                return self.inq[node_mac_addr].get(timeout=0)
            except Empty:
                return ""

    def send(self, data):
        try:
            self.interface.sendto(data, ('255.255.255.255', self.port))
        except Exception as e:
            print "sending failed at link level %s" % e
            time.sleep(0.01)
            self.send(data)

    def stop(self):
        self.keep_listening = False
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
        self.name = name if not name is None else self.mac_addr

        for link in network_links:
            self.add_interface(link)

    def __repr__(self):
        return "["+self.name+"]"

    def run(self):
        """networking loop init, this gets called on node.start()"""
        while self.keep_listening:
            for iface in self.interfaces:
                data = iface.recv(self.mac_addr)
                if data:
                    self.parse(data)
        self.log("Stopped listening.")

    def stop(self):
        self.keep_listening = False
        for i in self.interfaces:
            i.deregister(self.mac_addr)

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
        interface.register(self.mac_addr)
        self.interfaces += [interface]

    def log(self, *args):
        """stdout and stderr for the node"""
        print("%s %s" % (self, " ".join([ str(x) for x in args])))
        
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
    
    link = HardLink("en1", 2003)
    link.start()
    node = Node([link])
    node.start()

    try:
        while True:
            message = raw_input()
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
