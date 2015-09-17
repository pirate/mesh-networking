# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.5"
import traceback
import time
import random

from node import VirtualLink, HardLink, Node

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
    return [ node for node in nodes if link in node.interfaces ]

def eigenvalue(nodes, node=None):
    """
    calculate the eigenvalue (number of connections) for a given node in an array of nodes connected by an array of links
    if no node is given, return the minimum eigenvalue in the whole network
    """
    if node is None:
        return sorted([eigenvalue(nodes, n) for n in nodes])[0] # return lowest eigenvalue
    else:
        return len([1 for n in nodes if hops(node, n)])

def fmt(type, value, fallback=None):
    try:
        return type(value)
    except Exception:
        return fallback

def even_eigen_randomize(nodes, links, min_eigen=1):
    print("Introducing %s antisocial nodes to the party." % len(nodes))
    for node in nodes:
        while len(node.interfaces) < desired_min_eigenvalue:
            node.interfaces.append(random.choice(links))

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
    hardware_iface = 'en0'
    port = 2016
    if len(sys.argv) > 1:
        hardware_iface = sys.argv[1]

    num_nodes = fmt(int, input("How many nodes do you want? (14):"), 14)
    num_links = fmt(int, input("How many links do you want? (6):"), 6)
    real_link = str(input("Link to %s:%s too? (y/n):" % (hardware_iface, port)))[:1].lower() == "y"
    randomize = not str(input("Randomize links? (y/n)"))[:1].lower() == "n"
    
    links = [ HardLink(hardware_iface, port) ] if real_link else [ VirtualLink("l0") ]
    links += [ VirtualLink("l%s" % (x+1)) for x in range(num_links-1) ]

    nodes = [ Node(None, "n%s" % x) for x in range(num_nodes) ]

    desired_min_eigenvalue = min(max(1, len(nodes)-2), num_links)  # must be less than the total number of nodes!!!

    if randomize:
        even_eigen_randomize(nodes, links, desired_min_eigenvalue)
            
    print("Let there be life.")

    [link.start() for link in links]
    for node in nodes:
        node.start()
        print("%s:%s" % (node, node.interfaces))

    dont_exit = True

    print(help_str)
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
            print("Stopping Nodes")
            for node in nodes:
                node.stop()
            print("Stopping Links")
            for link in links:
                link.stop()
        except Exception as e:
            traceback.print_exc()
            print("EXITING BADLY")
            raise SystemExit(1)
        print("EXITING CLEANLY" if intentional else "EXITING BADLY")
        raise SystemExit(int(not intentional))

"""

   ^      \/
   |      |
   |      |
   \      /
    \    /
     \  /
      |
       |
      |
       |
      |
       |
      |
       |        < 4 bits can be sent in one clock tick
      |                 - 2b up
       |                - 2b down
      |
       |          or
      |
       |                - 1b up and 1b down in one tick


two cables, each cable can transmit one packet per tick
in order to switch transmission directions there is a
small latency between ticks.

this is a graph of the cable's state over time (time increases going down)
^ means the traffic is going up; , means it's going down

|^||^| time = 2 ticks; up, down = 2,2
------       1 tick delay for each direction switch
|,||,|
------
|^||^|
------
|,||,|
------       wasted tick is the time it takes the line to empty the buffer holding the packet
|^||^|
------
|,||,|
------
|^||^|
------
|,||,|
------
|^||^|

|,||^| time = 2 ticks; up, down = 2,2
|,||^|       no delay
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|       meanwhile, there are no --pauses-- because packets can be streamed one after another, crammed in tight
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
on seperate wires will always beat two single time-sharing duplex cables

of course, the wasted time will be much lower on a short line (probably in the <1ms range), but on longer cables
it can probably grow to >1ms, which really slows down an ethernet cable trying to run at 100mbps.


 """
