from collections import defaultdict
from time import sleep
import threading
from queue import Empty

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
