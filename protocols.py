from collections import defaultdict

class BaseFilter:
    @staticmethod
    def tr(self, packet, interface):
        return packet
    @staticmethod
    def tx(self, packet, interface):
        return packet

class DuplicateFilter(BaseFilter):
    """filter sending/receiving duplicates of the same packet in a row"""
    def __init__(self):
        self.last_sent = defaultdict(str)
        self.last_recv = defaultdict(str)

    def tr(self, packet, interface):
        if not packet or packet == self.last_recv[interface]:
            return None
        else:
            self.last_recv[interface] = packet
            return packet

    def tx(self, packet, interface):
        if not packet or packet == self.last_sent[interface]:
            return None
        else:
            self.last_sent[interface] = packet
            return packet

class LoopbackFilter(BaseFilter):
    """filter recieving copies of packets that the node just sent out"""
    def __init__(self):
        self.sent_hashes = defaultdict(int)

    def tr(self, packet, interface):
        if not packet:
            return None
        elif self.sent_hashes[hash(packet)] > 0:
            self.sent_hashes[hash(packet)] -= 1
            return None
        else:
            return packet

    def tx(self, packet, interface):
        if not packet:
            return None
        else:
            self.sent_hashes[hash(packet)] += 1
            return packet

class StringFilter(BaseFilter):
    """filter for packets that contain a pattern string"""
    def __init__(self, pattern='', inverse=False):
        self.pattern = pattern
        self.inverse = inverse

    def tr(self, packet, interface):
        if not packet:
            return None
        if not self.inverse:
            return packet if self.pattern in packet else None
        else:
            return packet if not self.pattern in packet else None 

class PrintProtocol:
    def __init__(self, node):
        self.node = node

    def recv(self, packet, interface):
        self.node.log("Printing packet:", packet)

class SwitchProtocol:
    def __init__(self, node, silent=False):
        self.node = node
        self.silent = silent

    def recv(self, packet, interface):
        other_ifaces = set(self.node.interfaces) - {interface}
        if not self.silent:
            self.node.log("SWITCH  ", (str(interface)+" >>>> <"+','.join(i.name for i in other_ifaces)+">").ljust(30), packet)
        self.node.send(packet, interfaces=other_ifaces)

class MeshProtocol:
    def __init__(self):
        self.listeners["syn"] = self.respond__hello
        self.listeners["SYN"] = self.respond__hello
        self.listeners["PAN"] = self.respond__hello
        self.listeners["KILL"] = self.stop
        self.listeners["kill"] = self.stop

    mesh_header = ";MESHPBEGIN;"            # beginnings of the MESHP protocol
    mesh_footer = ";MESHPEND;"

    def request__hello(self):
        self.broadcast("SYN")
        self.add_listener(pattern="ACK", callback=process_hello_response)

    def respond__hello(self, packet, *args):
        self.broadcast("ACK")


# [c9:f6:24:4b:1e:6e] IN  ('{"id":"1f5ff4bc2416cf63f03bdb14242710be63da84c4","origin_peer":{"id":"B","address":"10.0.5.33:3003","connected_peers":[{"id":"A","address":"10.0.5.33:3001"},{"id":"C","address":"10.0.5.33:7666","connected_peers":[{"id":"D","address":"10.0.5.33:1111"}]}]},"destination_id":""}', ('10.0.5.33', 53934))
