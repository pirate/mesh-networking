# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.2"   
import time

from node import VirtualLink, HardLink, Node

if __name__ == "__main__":
    red, green, blue = HardLink("en1"), VirtualLink(), VirtualLink()

    nodes = [Node([red, green, blue]),
             Node([red, green]),
             Node([green, blue]),
             Node([blue]),
             Node([blue])
    ]

    for node in nodes:
        node.start()

    nodes[0].broadcast("HELLO")
