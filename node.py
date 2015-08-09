# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.3"

import sys
import random
import threading
import time
import select
from queue import Queue, Empty
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, SO_REUSEPORT

from protocols import MeshProtocol

random.seed(None)   # defaults to system time

class VirtualLink:
    name = ""
    keep_listening = True
    inq = {}

    def log(self, *args):
        """stdout and stderr for the node"""
        print("%s %s" % (self, " ".join([str(x) for x in args])))

    def __repr__(self):
        return "<"+self.name+">"

    def __init__(self, iface="vlan", port=None):
        self.name = iface
        self.log("ready.")

    def register(self, node_mac_addr):
        if str(node_mac_addr) not in self.inq:
            self.inq[str(node_mac_addr)] = Queue()

    def deregister(self, node_mac_addr):
        if str(node_mac_addr) in self.inq:
            self.inq.pop(str(node_mac_addr))

    def recv(self, node_mac_addr):
        if self.keep_listening:
            try:
                data = self.inq[str(node_mac_addr)].get(timeout=0)
                return data
            except (KeyError, Empty):
                return ""

    def send(self, data):
        if self.keep_listening:
            for addr, nodeq in self.inq.items():
                nodeq.put(data)

    def stop(self):
        self.keep_listening = False
        self.log("went down.")

    def join(self):
        pass

    def start(self):
        pass

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

    def log(self, *args):
        """stdout and stderr for the link"""
        print("%s %s" % (self, " ".join([str(x) for x in args])))

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
        self.interface.bind(('', port))

        self.log("starting...")

    def register(self, node_mac_addr):
        if str(node_mac_addr) not in self.inq:
            self.inq[str(node_mac_addr)] = Queue()

    def deregister(self, node_mac_addr):
        if str(node_mac_addr) in self.inq:
            self.inq.pop(str(node_mac_addr))

    def run(self):
        self.log("ready.")
        last_packet = ("", "")
        while self.keep_listening:
            try:
                r, w, x = select.select([self.interface], [], [], 0.2)
            except Exception:
                # catch timeouts
                r = []
            for i in r:
                data, addr = i.recvfrom(4096)
                if addr[1] == self.port and (data, addr) != last_packet:
                    for _, nodeq in self.inq.items():
                        nodeq.put((data, addr))
                else:
                    # packet got filtered
                    pass
                last_packet = (data, addr)
            time.sleep(0.01)

    def recv(self, node_mac_addr):
        if self.keep_listening:
            try:
                return self.inq[str(node_mac_addr)].get(timeout=0)
            except (KeyError, Empty):
                return ""

    def send(self, data):
        try:
            self.interface.sendto(data, ('255.255.255.255', self.port))
        except Exception as e:
            self.log("sending failed at link level %s" % e)
            time.sleep(0.01)
            self.send(data)

    def stop(self):
        self.keep_listening = False
        self.log("went down.")
        self.join()

class Node(threading.Thread, MeshProtocol):
    interfaces = []
    keep_listening = True
    mac_addr = "de:ad:be:ef:de:ad"
    ip_addr = "eeee:::::::1"
    own_addr = "fasdfsdafsa"

    def __init__(self, network_links=None, name=None):
        network_links = [] if network_links is None else network_links
        MeshProtocol.__init__(self)
        threading.Thread.__init__(self)
        self.mac_addr = self.__genaddr__(6, 2)
        self.ip_addr = self.__genaddr__(8, 4)
        self.name = name if name is not None else self.mac_addr

        for link in network_links:
            self.add_interface(link)

    def __repr__(self):
        return "["+self.name+"]"

    def run(self):
        """networking loop init, this gets called on node.start()"""
        for iface in self.interfaces:
            self.add_interface(iface)
        while self.keep_listening:
            for iface in self.interfaces:
                data = iface.recv(self.mac_addr)
                if data:
                    self.recv(data)
            time.sleep(0.01)
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
                sub += random.choice("0123456789abcdef")
            addr.append(sub)
        return ":".join(addr)

    def add_interface(self, interface):
        interface.register(self.mac_addr)
        if interface not in self.interfaces:
            self.interfaces += [interface]

    def log(self, *args):
        """stdout and stderr for the node"""
        print("%s %s" % (self, " ".join([str(x) for x in args])))
        
    def recv(self, packet):
        self.log("IN ", packet)
        for pattern, callback in self.listeners.items():
            if pattern in packet:
                try:
                    callback(packet)
                except TypeError:
                    callback()

    def send(self, packet, links=interfaces):
        """write packet to an interface or several interfaces"""
        self.log("OUT", (packet, ("255.255.255.255", ",".join([i.name for i in self.interfaces]))))
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
    interface = "en1"
    if(len(sys.argv) > 1):
        interface = sys.argv[1]
    link = HardLink(interface, 2003)
    node = Node([link])
    link.start()
    node.start()

    try:
        while True:
            message = input(">")
            node.broadcast(message)
            time.sleep(0.5)

    except (EOFError, KeyboardInterrupt):
        node.stop()
        link.stop()
        node.join()
        link.join()
        print("EXITING")
        exit(0)


# [c9:f6:24:4b:1e:6e] IN  ('{"id":"1f5ff4bc2416cf63f03bdb14242710be63da84c4","origin_peer":{"id":"B","address":"10.0.5.33:3003","connected_peers":[{"id":"A","address":"10.0.5.33:3001"},{"id":"C","address":"10.0.5.33:7666","connected_peers":[{"id":"D","address":"10.0.5.33:1111"}]}]},"destination_id":""}', ('10.0.5.33', 53934))
