#!/usr/bin/env python3
# MIT Liscence : Serg Kondrashov
# ver : 0.1
import cmd
from multinode import *
from pdb import Restart

class Cli(cmd.Cmd):
    def __init__(self, default=True):
        """creation of nodes and links"""
        print("\n\n" + '='*80)
        cmd.Cmd.__init__(self)
        self.prompt = "> "
        self.intro = """type 'help' to show availible commands"""
        self.doc_header = "Availible commands (type 'help _command_' to get command help):"
        
        if not default:
            num_nodes = fmt(int, input("How many nodes do you want? [5]:"), 5)
            num_links = fmt(int, input("How many links do you want? [10]:"), 10)
            bridge = fmt(int, input("Link to wifi too, if so, on what port? (0 for no/#)[no]:"), False)
            randomize = not str(input("Randomize links, or play God? (r/g)[r]"))[:1].lower() == "g"
        else:
            num_nodes = 5
            num_links = 10
            bridge = False
            randomize = True

        self.links = [ HardLink("en1", bridge) ] if bridge else [ VirtualLink("l0") ]
        self.links += [ VirtualLink("l%s" % (x+1)) for x in range(num_links-1) ]

        self.nodes = [Node(None, "n%s" % x) for x in range(num_nodes)]
        
        desired_min_eigenvalue = 2  # must be less than the total number of nodes!!!
    
        if randomize:
            even_eigen_randomize(self.nodes, self.links, desired_min_eigenvalue)
            
        for link in self.links:
            link.start()
        for node in self.nodes:
            node.start()
            #print("%s:%s" % (node, node.interfaces))
        print("[info]\tAll nodes and links are started")
        
    def do_n(self, args):
        try:
            idx = int(args[0])
        except ValueError:
            idx = -1
        if -1 < idx < len(self.nodes):
            node = self.nodes[idx]
            message = str(input("%s<%s> ∂%s:" % (node, node.interfaces, eigenvalue(self.nodes, node))))
            if message == "stop":
                node.stop()
            else:
                node.broadcast(message)
        else:
            print("Not a node.")
    
    def do_node(self, args):
        do_n(self, args)
        
    def do_l(self, args):
        """type 'link 0' to choose <link 0>, then:
    type 'stop' to stop this link
    type '..' to cancel
    or type text to send to the link"""
        try:
            idx = int(args[0])
        except ValueError:
            idx = -1
        if -1 < idx < len(self.links):
            link = self.links[idx]
            link_members = linkmembers(self.nodes, link)
            message = str(input("%s(%s) %s>" % (link, len(link_members), link_members)))
            if message == "stop":
                link.stop()
            elif message == "..":
                pass
            else:
                link.send(message)
        else:
             print("Not a link.")
             
    def do_link(self, args):
        """type 'link 0' to choose <link 0>, then:
    type 'stop' to stop this link
    type '..' to cancel
    or type text to send to the link"""
        self.do_l(self, args)
             
    def do_list(self, args):
        """show availible nodes with it's links"""
        print('current nodes:')
        for n in self.nodes:
            print('{0} : {1}'.format(n, n.interfaces))
            
    def do_exit(self, args):
        """stop all nodes and links and exit"""
        try:
            print("Stopping Nodes")
            for node in self.nodes:
                node.stop()
                node.join()
            print("Stopping Links")
            for link in self.links:
                link.stop()
                link.join()
        except Exception as e:
            traceback.print_exc()
            print("EXITING BADLY")
            raise SystemExit(1)
        print("EXITING CLEANLY")
        raise SystemExit(0)     
    
    def do_get_neighbors(self, args):
        if self.get_node(args):
            start_node = self.get_node(args)
            wieght, path = dijkstra(self.nodes, start_node)
            print(wieght)
            print(path)
        else:
            print("'{0}' is not a node!".format(args))
            
    def default(self, line):
        print("???")
        
    def emptyline(self):
        pass
    
    def get_node(self, args):
        a = cmd.Cmd.parseline(self, args)[0]
        try:
            idx = int(a[1:])
        except ValueError:
            idx = -1
        if -1 < idx < len(self.nodes):
            return self.nodes[idx]
        else:
            return False
            
if __name__ == '__main__':
    if input("run default? y/n [y]:") != "n":
        d = True
    else:
        d = False
    cli = Cli(d)
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print('exit...') 
