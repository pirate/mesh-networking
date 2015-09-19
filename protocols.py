from collections import defaultdict
from time import sleep
import threading
from queue import Empty

class BaseFilter:
    """Filters work just like iptables filters, they are applied in order to all incoming and outgoing packets
       Filters can return a modified packet, or None to drop it
    """
    @classmethod
    def tr(self, packet, interface):
        """tr is shorthand for receive filter method
            incoming node packets are filtered through this function before going in the inq
        """
        return packet
    @classmethod
    def tx(self, packet, interface):
        """tx is send filter method
            outgoing node packets are filtered through this function before being sent to the link
        """
        return packet

class DuplicateFilter(BaseFilter):
    """filter sending/receiving duplicates of the same packet in a row.
    
        This is an example of a stateful filter, it needs to remember 
        last_sent and last_recv between packet recvs.
    """
    def __init__(self):
        self.last_sent = defaultdict(str)  # defaults to ""
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
    """Filter recv copies of packets that the node just sent out.
        Needed whenever your node is connected to a BROADCAST link where all packets go to everyone.
    """
    def __init__(self):
        self.sent_hashes = defaultdict(int)  # defaults to 0
        # serves as a counter. each packet is hashed,
        # if we see that hash sent once we can ignore once receive copy,
        # if we send it twice on two ifaces, we can ignore two received copies

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
    """Filter for packets that contain a string pattern.
        Node('mynode', Filters=[StringFilter.match('pattern'), ...])
    """
    def tr(self, packet, interface):
        if not packet:
            return None
        if not self.inverse:
            return packet if self.pattern in packet else None
        else:
            return packet if self.pattern not in packet else None

    @classmethod
    def match(cls, pattern, inverse=False):
        """Call this before passing to node to set up this stateless but dynamic filter."""
        cls.pattern = pattern
        cls.inverse = inverse
        return cls

    @classmethod
    def dontmatch(cls, pattern):
        return cls.match(pattern, inverse=True)


class BaseProtocol(threading.Thread):
    """Protocols represent a program running on a Node.
    They serve to processes the incoming network packets in a seperate thread."""
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
    """A simple Protocol to just print incoming packets to the console."""
    def recv(self, packet, interface):
        self.node.log(("PROTOCOL "+str(interface)).ljust(39), packet.decode())

class SwitchProtocol(BaseProtocol):
    """A switch that routes a packet coming in on any interface to all the other interfaces."""
    def recv(self, packet, interface):
        other_ifaces = set(self.node.interfaces) - {interface}
        self.node.log("SWITCH  ", (str(interface)+" >>>> <"+','.join(i.name for i in other_ifaces)+">").ljust(30), packet.decode())
        self.node.send(packet, interfaces=other_ifaces)

# [c9:f6:24:4b:1e:6e] IN  ('{"id":"1f5ff4bc2416cf63f03bdb14242710be63da84c4","origin_peer":{"id":"B","address":"10.0.5.33:3003","connected_peers":[{"id":"A","address":"10.0.5.33:3001"},{"id":"C","address":"10.0.5.33:7666","connected_peers":[{"id":"D","address":"10.0.5.33:1111"}]}]},"destination_id":""}', ('10.0.5.33', 53934))
