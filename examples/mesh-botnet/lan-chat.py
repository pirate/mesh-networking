# -*- coding: utf-8 -*-
# MIT License: Nick Sweeting
import time

from ..links import UDPLink
from ..programs import Printer
from ..filters import UniqueFilter
from ..node import Node

if __name__ == "__main__":
    print("Run lan-chat.py on another laptop to talk between the two of you on en0.")

    # links = [UDPLink('en0', 2010), UDPLink('en1', 2011), UDPLink('en2', 2012), UDPLink('en3', 2013)]
    links = [UDPLink('en1', 2012)]
    node = Node(links, 'me', Program=Printer)
    [link.start() for link in links]
    node.start()

    try:
        while True:
            print("------------------------------")
            message = input("[me]  OUT:".ljust(49))
            node.send(bytes(message, 'UTF-8'))
            time.sleep(1)

    except (EOFError, KeyboardInterrupt):   # CTRL-D, CTRL-C
        node.stop()
        [link.stop() for link in links]
