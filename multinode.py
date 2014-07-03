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

    try:
        while True:
            node = int(raw_input())
            message = raw_input()
            if message == "stop":
                raise KeyboardInterrupt
            else:
                nodes[node].broadcast(message)
            time.sleep(0.5)

    except KeyboardInterrupt:
        for node in nodes:
            node.stop()
        red.stop()
        print("EXITING")
        exit(0)
