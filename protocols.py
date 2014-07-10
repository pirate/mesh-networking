class BaseProtocol:
    listeners = {}

    def broadcast(*args, **kwargs):
        pass
    def send(*args, **kwargs):
        pass
    def receive(*args, **kwargs):
        pass
    def ignore(*args, **kwargs):
        pass

    def add_listener(self, pattern, callback):
        """wait for packets matching a pattern, and feed them into their proper callback"""
        self.listeners[pattern] = callback

    def remove_listener(self, pattern):
        """stop monitoring for packets that match a given pattern"""
        self.listeners.pop(pattern)

class MeshProtocol(BaseProtocol):
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

class JSONMeshProtocol(BaseProtocol):
    def __init__():
        self.listeners["ACK"] = self.respond__hello
        self.listeners["HELLO"] = self.respond__hello
        self.listeners["PAN"] = self.respond__hello
        self.listeners["KILL"] = self.stop

    def request__hello(self):
        self.broadcast("SYN")
        self.add_listener(pattern="ACK", callback=process_hello_response)

    def respond__hello(self, packet):
        self.broadcast(";ACK %s;" % packet)
