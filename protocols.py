from scapy.all import Packet, Ether, TCP, StrField, ShortField, XByteField, IntEnumField


class MeshIP(Packet):
    name = 'MeshIP'
    fields_desc = [
        ShortField('source', None),
        ShortField('target', None),
    ]


class MeshARP(Packet):
    name = 'MeshARP'
    fields_desc = [
        IntEnumField('mode', 1,
            {1: 'QUERY', 2: 'ANNOUNCE'}
        ),
        ShortField('target', 5),
    ]


class HumanARP(Packet):
    name = 'HumanARP'
    fields_desc = [
        IntEnumField('mode', 1,
            {1: 'QUERY', 2: 'ANNOUNCE'}
        ),
        ShortField('target', 5),
    ]

class HumanIRC(Packet):
    name = 'HumanIRC'
    fields_desc = [
        StrField('action', ''),
    ]


if __name__ == '__main__':
    test_packet = (Ether() /
                   MeshIP(source=0, target=2) /
                   TCP() /
                   'hi')

    test_packet.show()
    print(bytes(test_packet))

