from collections import defaultdict
import time
import random
import hashlib

class BaseFilter:
    """Filters work just like iptables filters, they are applied in order to all incoming and outgoing packets
       Filters can return a modified packet, or None to drop it
    """

    # stateless filters use classmethods, stateful filters should add an __init__
    @classmethod
    def tr(self, packet, interface):
        """tr is shorthand for receive filter method
            incoming node packets are filtered through this function before going in the inq
        """
        return packet
    @classmethod
    def tx(self, packet, interface):
        """tx is send filter method
            outgoing node packets are filtered through this function before being sent to the link
        """
        return packet

class DuplicateFilter(BaseFilter):
    """filter sending/receiving duplicates of the same packet in a row.

        This is an example of a stateful filter, it needs to remember
        last_sent and last_recv between packet recvs.
    """
    def __init__(self):
        self.last_sent = defaultdict(str)  # defaults to ""
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
    """Filter recv copies of packets that the node just sent out.
        Needed whenever your node is connected to a BROADCAST link where all packets go to everyone.
    """
    def __init__(self):
        self.sent_hashes = defaultdict(int)  # defaults to 0
        # serves as a counter. each packet is hashed,
        # if we see that hash sent once we can ignore one received copy,
        # if we send it twice on two ifaces, we can ignore two received copies

    def tr(self, packet, interface):
        if not packet: return None
        elif self.sent_hashes[hash(packet)] > 0:
            self.sent_hashes[hash(packet)] -= 1
            return None
        else:
            return packet

    def tx(self, packet, interface):
        if not packet: return None
        else:
            self.sent_hashes[hash(packet)] += 1
            return packet

class UniqueFilter(BaseFilter):
    def __init__(self):
        self.seen = set()

    @staticmethod
    def hash(string):
        return hashlib.md5(string).hexdigest()

    def tr(self, packet, interface):
        if not packet:
            return None

        packet_hash = self.hash(packet)
        if packet_hash in self.seen:
            return None
        else:
            self.seen.add(packet_hash)
            return packet

    def tx(self, packet, interface):
        if not packet:
            return None

        packet_hash = self.hash(packet)
        self.seen.add(packet_hash)
        return packet

class StringFilter(BaseFilter):
    """Filter for packets that contain a string pattern.
        Node('mynode', Filters=[StringFilter.match('pattern'), ...])
    """
    def tr(self, packet, interface):
        if not packet: return None
        if not self.inverse:
            return packet if self.pattern in packet else None
        else:
            return packet if self.pattern not in packet else None

    @classmethod
    def match(cls, pattern, inverse=False):
        """Factory method to create a StringFilter which filters with the given pattern."""
        string_pattern = pattern
        invert_search = inverse

        class DefinedStringFilter(cls):
            pattern = string_pattern
            inverse = invert_search
        return DefinedStringFilter

    @classmethod
    def dontmatch(cls, pattern):
        return cls.match(pattern, inverse=True)
