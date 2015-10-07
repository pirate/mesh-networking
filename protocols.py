from collections import defaultdict
from queue import Empty

# TODO: Replace most of this file with Scapy's wonderful packet construction and deconstruction system

class Frame:
    """an ethernet frame"""
    def __init__(self, source_mac, dest_mac, protocol=None, data=''):
        self.source = source_mac.replace(':','')
        self.dest = dest_mac.replace(':','')
        assert len(self.source) == 12
        assert len(self.dest) == 12
        self.protocol = protocol or getattr(data, 'protocol', '')
        self.data = data

    def __repr__(self):
        return '[%s>%s %s:%s]' % (self.source, self.dest, self.protocol, self.data.__repr__())

    def __str__(self):
        return self.dest+self.source+str(self.protocol)+str(self.data)

class ARP:
    def __init__(self, asker, question):
        self.protocol = 'ARP'
        self.asker = asker
        self.question = question

    def __repr__(self):
        return '{%s? > %s}' % (self.question, self.asker)

    def __str__(self):
        return self.asker+self.question

class ICMP:
    def __init__(self, asker, question):
        self.protocol = 'ICMP'
        self.asker = asker
        self.question = question

    def __repr__(self):
        return '{%s? > %s}' % (self.question, self.asker)

    def __str__(self):
        return self.asker+self.question

# [c9:f6:24:4b:1e:6e] IN  ('{"id":"1f5ff4bc2416cf63f03bdb14242710be63da84c4","origin_peer":{"id":"B","address":"10.0.5.33:3003","connected_peers":[{"id":"A","address":"10.0.5.33:3001"},{"id":"C","address":"10.0.5.33:7666","connected_peers":[{"id":"D","address":"10.0.5.33:1111"}]}]},"destination_id":""}', ('10.0.5.33', 53934))
