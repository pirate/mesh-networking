# -*- coding: utf-8 -*-
# Nick Sweeting 2016/10/08
# Butterfly Network
#
# Simulate a butterfly network where addresses can be used to determine routing paths.
# MIT 6.042J Mathematics for Computer Science: Lecture 9
# https://www.youtube.com/watch?v=bTyxpoi2dmM

import math
import time

from mesh.node import Node
from mesh.links import VirtualLink
from mesh.programs import Cache, BaseProgram


class ButterflySwitch(BaseProgram):
    """A switch that routes a packet coming in on any interface to all the other interfaces."""
    def recv(self, packet, interface):
        other_ifaces = set(self.node.interfaces) - {interface}
        if packet and other_ifaces:
            self.node.log("SWITCH  ", (str(interface)+" >>>> <"+','.join(i.name for i in other_ifaces)+">").ljust(30), packet.decode())
            self.node.send(packet, interfaces=other_ifaces)


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

def print_grid(nodes):
    for row in NODES:
        output = ''
        if row and row[-1].program.received:
            output = ' : {}'.format(row[-1].program.received.pop())
        print(' --- '.join(str(n).center(10) for n in row) + output)


if __name__ == "__main__":
    num_rows = ask(int, "How many input nodes do you want?     [8]:", 8)
    num_cols = 2 + int(math.log(num_rows))

    print('Creating Nodes ({}x{})...'.format(num_rows, num_cols))

    IN_ADDRESSES = ['in:0b{0:b}'.format(a) for a in range(0, num_rows)]
    OUT_ADDRESSES = ['out:0b{0:b}'.format(a) for a in range(0, num_rows)]

    NODES = []

    # make several rows of input nodes to output nodes
    for row_idx in range(num_rows):
        row = []
        for col_idx in range(num_cols):
            # add input node
            if col_idx == 0:
                addr = IN_ADDRESSES[row_idx]
                Program = None
            # add output node
            elif col_idx == num_cols - 1:
                addr = OUT_ADDRESSES[row_idx]
                Program = Cache
            # out middle node
            else:
                addr = 'row:{};col{}'.format(row_idx, col_idx)
                Program = ButterflySwitch

            row.append(Node(name=addr, mac_addr=addr, Program=Program))

        NODES.append(row)


    print('Creating Butterfly Links...')

    # make the first links going directly across each row
    for row_idx in range(num_rows):
        for col_idx in range(num_cols - 1):
            bridge = VirtualLink(name='{}<{}>{}'.format(col_idx, row_idx, col_idx + 1))
            NODES[row_idx][col_idx].interfaces.append(bridge)

            # node directly to the right
            NODES[row_idx][col_idx + 1].interfaces.append(bridge)
            bridge.start()

    # TODO: finish diagonal linking algorithm
    # give each node a second diagonal link, starting from right to left
    for col_idx in reversed(range(1, num_cols)):
        for row_idx in range(num_rows):
            diagonal = VirtualLink(name='{}<{}>{}'.format(col_idx, row_idx, col_idx + 1))
            NODES[row_idx][col_idx].interfaces.append(diagonal)

            # node to the left and (up/down) to a different butterfly set
            to_row = 1
            NODES[to_row][col_idx - 1].interfaces.append(diagonal)
            diagonal.start()

    [n.start() for row in NODES for n in row]

    print_grid(NODES)

    print('Input the number of a node, followed by text to send')
    print('    e.g.  [$]: 0:hello world!')
    dont_exit = True
    try:
        while dont_exit:
            try:
                in_id, in_text = str(input("#:text ")).split(':', 1)
            except ValueError:
                print('Input must be #:text')
                continue
            in_node = NODES[int(in_id)][0]
            in_node.send(bytes(in_text, 'UTF-8'))
            time.sleep(0.2)
            # import ipdb; ipdb.set_trace()
            print_grid(NODES)
    except (KeyboardInterrupt, EOFError):
        raise SystemExit(0)
