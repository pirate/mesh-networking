#!/usr/bin/env python3
import time

from mesh.links import UDPLink
from mesh.programs import BaseProgram
from mesh.filters import UniqueFilter
from mesh.node import Node



class ChatProgram(BaseProgram):
    def recv(self, packet, interface):
        print('\n>> {}'.format(packet.decode()))


if __name__ == "__main__":
    links = [UDPLink('en0', 2010), UDPLink('en1', 2011), UDPLink('en2', 2012), UDPLink('en3', 2013)]
    node = Node(links, 'me', Filters=(UniqueFilter,), Program=ChatProgram)
    [link.start() for link in links]
    node.start()

    print("Run lan-chat.py on another laptop to talk between the two of you on en0.")
    try:
        while True:
            print("------------------------------")
            message = input('<< ')
            node.send(bytes(message, 'UTF-8'))
            time.sleep(0.3)

    except (EOFError, KeyboardInterrupt):   # graceful CTRL-D & CTRL-C
        node.stop()
        [link.stop() for link in links]
