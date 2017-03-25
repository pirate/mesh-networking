# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting

from time import sleep

from mesh.links import VirtualLink, UDPLink
from mesh.programs import Switch, Printer
from mesh.filters import DuplicateFilter, StringFilter
from mesh.node import Node


# ls = (UDPLink('en0', 2014), VirtualLink('vl1'), VirtualLink('vl2'), IRCLink('irc3'), UDPLink('en4', 2016), IRCLink('irc5'))          # slow, but impressive to connect over IRC
ls = (UDPLink('en0', 2010), VirtualLink('vl1'), VirtualLink('vl2'), UDPLink('irc3', 2013), UDPLink('en4', 2014), UDPLink('irc5', 2013))    # faster setup for quick testing
nodes = (
    Node([ls[0]], 'start'),
    Node([ls[0], ls[2]], 'l1', Program=Switch),
    Node([ls[0], ls[1]], 'r1', Program=Switch),
    Node([ls[2], ls[3]], 'l2', Filters=(DuplicateFilter,), Program=Switch),              # l2 wont forward two of the same packet in a row
    Node([ls[1], ls[4]], 'r2', Filters=(StringFilter.match(b'red'),), Program=Switch),   # r2 wont forward any packet unless it contains the string 'red'
    Node([ls[4], ls[5]], 'end', Program=Printer),
)
[l.start() for l in ls]
[n.start() for n in nodes]


if __name__ == "__main__":
    print("Using a mix of real and vitual links to make a little network...\n")
    print("          /[r1]<--vlan1-->[r2]<----vlan4---\\")
    print("[start]-en0                                [end]")
    print("          \[l1]<--vlan2-->[l2]<--irc3:irc5-/\n")


    print('\n', nodes)
    print("l2 wont forward two of the same packet in a row.")
    print("r2 wont forward any packet unless it contains the string 'red'.")
    print("Experiment by typing packets for [start] to send out, and seeing if they make it to the [end] node.")

    try:
        while True:
            print("------------------------------")
            message = input("[start]  OUT:".ljust(49))
            nodes[0].send(bytes(message, 'UTF-8'))
            sleep(1)

    except (EOFError, KeyboardInterrupt):   # CTRL-D, CTRL-C
        print(("All" if all([n.stop() for n in nodes]) else 'Not all') + " nodes stopped cleanly.")
        print(("All" if all([l.stop() for l in ls]) else 'Not all') + " links stopped cleanly.")
