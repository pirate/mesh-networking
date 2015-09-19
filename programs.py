import threading
from time import sleep
from queue import Empty

class BaseProgram(threading.Thread):
    """Represents a program running on a Node that responds to incoming packets.
    They serve to processes and route incoming traffic in a seperate thread."""
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

class Printer(BaseProgram):
    """A simple program to just print incoming packets to the console."""
    def recv(self, packet, interface):
        sleep(0.2)
        self.node.log(("PRINTER  "+str(interface)).ljust(39), packet.decode())

class Switch(BaseProgram):
    """A switch that routes a packet coming in on any interface to all the other interfaces."""
    def recv(self, packet, interface):
        other_ifaces = set(self.node.interfaces) - {interface}
        if packet and other_ifaces:
            self.node.log("SWITCH  ", (str(interface)+" >>>> <"+','.join(i.name for i in other_ifaces)+">").ljust(30), packet.decode())
            self.node.send(packet, interfaces=other_ifaces)
