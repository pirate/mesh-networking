from collections import defaultdict
from time import sleep
import threading
from queue import Empty

class BaseFilter:
    """Filters work just like iptables filters, they are applied in order to all incoming and outgoing packets
       Filters can return a modified packet, or None to drop it.
    """
    @classmethod
    def tr(self, packet, interface):
        return packet
    @classmethod
    def tx(self, packet, interface):
        return packet

class DuplicateFilter(BaseFilter):
    """filter sending/receiving duplicates of the same packet in a row
       This is an example of a stateful filter, it needs to remember last_sent and last_recv to filter duplicates
    """
    def __init__(self):
        self.last_sent = defaultdict(str)
        self.last_recv = defaultdict(str)

    def tr(self, packet, interface):
        if not packet or packet == self.last_recv[interface]:
            return None
        else:
            self.last_recv[interface] = packet
            return packet

    def tx(self, packet, interface):
        if not packet or packet == self.last_sent[interface]:
            return None
        else:
            self.last_sent[interface] = packet
            return packet

class LoopbackFilter(BaseFilter):
    """filter recieving copies of packets that the node just sent out"""
    def __init__(self):
        self.sent_hashes = defaultdict(int)

    def tr(self, packet, interface):
        if not packet:
            return None
        elif self.sent_hashes[hash(packet)] > 0:
            self.sent_hashes[hash(packet)] -= 1
            return None
        else:
            return packet

    def tx(self, packet, interface):
        if not packet:
            return None
        else:
            self.sent_hashes[hash(packet)] += 1
            return packet

class StringFilter(BaseFilter):
    """filter for packets that contain a pattern string"""
    def tr(self, packet, interface):
        if not packet:
            return None
        if not self.inverse:
            return packet if self.pattern in packet else None
        else:
            return packet if self.pattern not in packet else None

    @classmethod
    def match(cls, pattern, inverse=False):
        cls.pattern = pattern
        cls.inverse = inverse
        return cls

    @classmethod
    def dontmatch(cls, pattern):
        return cls.match(pattern, inverse=True)

class BaseProtocol(threading.Thread):
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.keep_listening = True
        self.node = node

    def run(self):
        """runloop that processes packets off the node's input queue"""
        while self.keep_listening:
            for interface in self.node.interfaces:
                try:
                    self.recv(self.node.inq[interface].get(timeout=0), interface)
                except Empty:
                    sleep(0.01)

    def stop(self):
        self.keep_listening = False
        self.join()

    def recv(self, packet, interface):
        """some logic here to actually do something with the packet"""
        pass

class PrintProtocol(BaseProtocol):
    def recv(self, packet, interface):
        self.node.log("Printing packet:", interface, packet)

class SwitchProtocol(BaseProtocol):
    def recv(self, packet, interface):
        other_ifaces = set(self.node.interfaces) - {interface}
        self.node.log("SWITCH  ", (str(interface)+" >>>> <"+','.join(i.name for i in other_ifaces)+">").ljust(30), packet)
        self.node.send(packet, interfaces=other_ifaces)

# [c9:f6:24:4b:1e:6e] IN  ('{"id":"1f5ff4bc2416cf63f03bdb14242710be63da84c4","origin_peer":{"id":"B","address":"10.0.5.33:3003","connected_peers":[{"id":"A","address":"10.0.5.33:3001"},{"id":"C","address":"10.0.5.33:7666","connected_peers":[{"id":"D","address":"10.0.5.33:1111"}]}]},"destination_id":""}', ('10.0.5.33', 53934))
