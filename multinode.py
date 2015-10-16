# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.8"
import traceback
import time
import random

from node import Node
from links import UDPLink, VirtualLink, IRCLink
from programs import Printer, Switch
from filters import UniqueFilter

def hops(node1, node2):
    """returns # of hops it takes to get from node1 to node2, 1 means they're on the same link"""
    if node1 == node2:
        return 0
    elif set(node1.interfaces) & set(node2.interfaces):
        # they share a common interface
        return 1
    else:
        # Not implemented yet, graphsearch to find min hops between two nodes
        return 0

def linkmembers(nodes, link):
    return [n for n in nodes if link in n.interfaces]

def eigenvalue(nodes, node=None):
    """
    calculate the eigenvalue (number of connections) for a given node in an array of nodes connected by an array of links
    if no node is given, return the minimum eigenvalue in the whole network
    """
    if node is None:
        return sorted([eigenvalue(nodes, n) for n in nodes])[0] # return lowest eigenvalue
    else:
        return len([1 for n in nodes if hops(node, n)])

def even_eigen_randomize(nodes, links, min_eigen=1):
    print("Linking %s together randomly." % len(nodes))
    for node in nodes:
        while len(node.interfaces) < ((desired_min_eigenvalue - random.randint(0, 3)) or 1):
            node.interfaces.append(random.choice(tuple(set(links) - set(node.interfaces))))

def ask(type, question, fallback=None):
    value = input(question)
    if type == bool:
        if fallback:
            return not value[:1].lower() == "n"
        else:
            return value[:1].lower() == "y"
    try:
        return type(value)
    except Exception:
        return fallback

help_str = """Type a nodelabel or linkname to send messages.
        e.g. [$]:n35
             [n35]<en1> ∂5:hi
        or
             [$]:l5
             <l5>(3) [n1,n4,n3]:whats up"""

if __name__ == "__main__":
    import sys
    # import netifaces
    # hardware_iface = netifaces.gateways()['default'][2][1]
    port = 2016
    # if len(sys.argv) > 1:
        # hardware_iface = sys.argv[1]

    num_nodes = ask(int,  "How many nodes do you want?     [30]:",      30)
    num_links = ask(int,  "How many links do you want?      [8]:",       8)
    irc_link  = ask(bool, "Link to internet?              y/[n]:",   False)
    real_link = ask(bool, "Link to local networks?        [y]/n:",    True)
    randomize = ask(bool, "Randomize connections?         [y]/n:",    True)
    
    print('Creating Links...')
    links = []
    if real_link:
        links += [UDPLink('en0', port), UDPLink('en1', port+1), UDPLink('en2', port+2)]
    if irc_link:
        links += [IRCLink('irc0')]
    links += [ VirtualLink("vl%s" % (x+1)) for x in range(num_links) ]

    print('Creating Nodes...')
    nodes = [ Node(None, "n%s" % x, Filters=[UniqueFilter], Program=random.choice((Printer, Switch))) for x in range(num_nodes) ]

    if randomize:
        desired_min_eigenvalue = 4 if 4 < num_links else len(links)-2 # must be less than the total number of nodes!!!
        even_eigen_randomize(nodes, links, desired_min_eigenvalue)
            
    print("Let there be life.")
    [link.start() for link in links]
    for node in nodes:
        node.start()
        print("%s:%s" % (node, node.interfaces))

    print(help_str)
    dont_exit = True
    try:
        while dont_exit:
            command = str(input("[$]:"))
            if command[:1] == "l":
                # LINK COMMANDS
                link = [l for l in links if l.name[1:] == command[1:]]
                if link:
                    link = link[0]
                    link_members = linkmembers(nodes, link)
                    message = str(input("%s(%s) %s:" % (link, len(link_members), link_members)))
                    if message == "stop":
                        link.stop()
                    else:
                        link.send(bytes(message, 'UTF-8'))  # convert python str to bytes for sending over the wire
                else:
                    print("Not a link.")
                
            elif command[:1] == "n":
                # NODE COMMANDS
                node = [n for n in nodes if n.name[1:] == command[1:]]
                if node:
                    node = node[0]
                    message = str(input("%s<%s> ∂%s:" % (node, node.interfaces, eigenvalue(nodes, node))))
                    if message == "stop":
                        node.stop()
                    else:
                        node.send(bytes(message, 'UTF-8'))  # convert python str to bytes for sending over the wire
                else:
                    print("Not a node.")
                
            elif command[:1] == "h":
                print(help_str)
            else:
                print("Invalid command.")
                print(help_str)

            time.sleep(0.5)
    except BaseException as e:
        intentional = type(e) in (KeyboardInterrupt, EOFError)
        if not intentional:
            traceback.print_exc()
        try:
            assert all([n.stop() for n in nodes]), 'Some nodes failed to stop.'
            assert all([l.stop() for l in links]), 'Some links failed to stop.'
        except Exception as e:
            traceback.print_exc()
            intentional = False
        print("EXITING CLEANLY" if intentional else "EXITING BADLY")
        raise SystemExit(int(not intentional))

"""
ETHERNET CABLE DUPLEXING:

least efficient (10BASE-2 half-duplex):
    
       ^      \/    single line half-duplex with tr and tx taking turns
       ^      ,
       ^      ,
       ^      ,
        ^    ,
         ^  ,
          ^         1 tick tx
           ,        1 tick tr
          ^
           ,
          ^
           ,
          ^
           ,        4 bits can be sent in one clock tick
          ^         2b up
           ,        2b down
          ^
           ,
          ^
           ,


medium efficieny (1000BASE-T half-duplex):
    two lines, each line can transmit one packet per tick
    in order to switch transmission directions there is a
    small latency between ticks.

    this is a graph of the cable's state over time (time increases going down)
    ^ means the traffic is going up; , means it's going down

    |^||^|          |^||^| = 1 tick where both cables are tx-ing
    ------          ------ = 1 tick delay for each direction switch
    |,||,|          |,||,| = 1 tick where both cables are tr-ing
    ------
    |^||^|
    ------
    |,||,|
    ------          wasted tick is the time it takes the line to empty the buffer holding the packet
    |^||^|
    ------
    |,||,|
    ------
    |^||^|
    ------
    |,||,|
    ------
    |^||^|

highest efficiency (100BASE-TX full-duplex):
    |,||^|       one line is pure tx, and one is pure tr
    |,||^|       no direction switch delay
    |,||^|
    |,||^|
    |,||^|
    |,||^|
    |,||^|
    |,||^|       there are no --pauses-- because packets can be streamed one after another, crammed in tight
    |,||^|
    |,||^|
    |,||^|
    |,||^|
    |,||^|
    |,||^|
    |,||^|
    |,||^|
    |,||^|

    thus, in the same amount of time, a full-duplex setup where up and down are split
    on seperate wires will always beat two single time-sharing half-duplex cables

    of course, the wasted time will be much lower on a short line (probably in the <1ms range), but on longer cables
    it can probably grow to >1ms, which really slows down an ethernet cable trying to run at 100mbps.

Newer models of routers, hubs and switches can automatically switch between a "straight-through" and a "crossover" set-up, doing away with the need to use two different Cat5 cables.
"""
