import re
import threading
from time import sleep

try:
    from queue import Empty
except ImportError:
    from Queue import Empty

from .routers import MessageRouter


class BaseProgram(threading.Thread):
    """Represents a program running on a Node that interprets and responds to incoming packets."""
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.keep_listening = True
        self.node = node

    def run(self):
        """runloop that reads packets off the node's incoming packet buffer (node.inq)"""
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
        """overload this and put logic here to actually do something with the packet"""
        pass

class Printer(BaseProgram):
    """A simple program to just print incoming packets to the console."""
    def recv(self, packet, interface):
        sleep(0.2)  # nicety so that printers print after all the debug statements
        self.node.log(("PRINTER  %s" % interface).ljust(39), packet.decode())

class Switch(BaseProgram):
    """A switch that routes a packet coming in on any interface to all the other interfaces."""
    def recv(self, packet, interface):
        other_ifaces = set(self.node.interfaces) - {interface}
        if packet and other_ifaces:
            self.node.log("SWITCH  ", (str(interface)+" >>>> <"+','.join(i.name for i in other_ifaces)+">").ljust(30), packet.decode())
            self.node.send(packet, interfaces=other_ifaces)

class Cache(BaseProgram):
    """A simple program to which stores incoming packets in a buffer indefinitely."""
    def __init__(self, node):
        self.received = []
        BaseProgram.__init__(self, node)

    def recv(self, packet, interface):
        self.received.append(packet)


def R(pattern):
    return re.compile(pattern)

class RoutedProgram(BaseProgram):
    """Base program which easily routes messages to handler functions.

    usage:
        class MyProgram(RoutedProgram):
            router = RoutedProgram.router

            @router.route(R('^HELLO$'))
            def handle_hello(self, packet, interface):
                self.send('How are you?', interface)
    """
    router = MessageRouter()

    def __init__(self, node):
        super(RoutedProgram, self).__init__(node)
        self.router.node = node

    def recv(self, packet, interface):
        message = packet.decode()
        self.node.log('\n< [RECV]  %s' % message)
        self.router.recv(self, message, interface)

    def send(self, message, interface):
        if not (hasattr(message, '__iter__') and not hasattr(message, '__len__')):
            # if message is not a list or generator
            message = [message]

        for line in message:
            line = line if type(line) in (str, bytes) else '{0}'.format(line)
            if not line.strip():
                continue

            self.node.log('\n> [SENT]  %s' % line)
            packet = bytes(line, 'utf-8') if type(line) is str else line
            self.node.send(packet, interface)
