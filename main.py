#!/usr/bin/env python3
# MIT Liscence : Serg Kondrashov
# ver : 0.13

import cmd
from multinode import *
from asyncio.tasks import sleep

class Cli(cmd.Cmd):
    def __init__(self, default=True):
        """creation of nodes and links"""
        print("\n\n" + '='*80)
        cmd.Cmd.__init__(self)
        self.prompt = "> "
        self.intro = """type 'help' to show availible commands\ntype 'all' to view all nodes with links"""
        self.doc_header = "Availible commands (type 'help _command_' to get command help):"
        
        if not default:
            num_nodes = fmt(int, input("How many nodes do you want? [5]:"), 5)
            num_links = fmt(int, input("How many links do you want? [10]:"), 10)
            bridge = fmt(int, input("Link to wifi too, if so, on what port? (0 for no/#)[no]:"), False)
            randomize = not str(input("Randomize links, or play God? (r/g)[r]"))[:1].lower() == "g"
            direct_links = not str(input("One link only for 2 nodes? (y/n)[y]"))[:1].lower() == "n"
            min_links = fmt(int, input("What is minimum of links in one node? [1]:"), 1)
            max_links = fmt(int, input("What is maximum of links in one node? [5]:"), 5)
        else:
            num_nodes = 5
            num_links = 10
            bridge = False
            randomize = True
            direct_links = True
            min_links = 1
            max_links = 5

        self.links = [ HardLink("en1", bridge) ] if bridge else [ VirtualLink("l0") ]
        self.links += [ VirtualLink("l%s" % (x+1)) for x in range(num_links-1) ]

        self.nodes = [Node(None, "n%s" % x) for x in range(num_nodes)]
        
        if randomize:
            even_eigen_randomize(self.nodes, self.links, direct_links, min_links, max_links)
            
        for link in self.links:
            link.start()
        for node in self.nodes:
            node.start()
            #print("%s:%s" % (node, node.interfaces))
        print("[info]\tAll nodes and links are started")
     
    def do_n(self, args):
        """node commands"""
        try:
            idx = int(args[0:])
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
        """node commands"""
        do_n(self, args)
        
    def do_l(self, args):
        """type 'link 0' to choose <link 0>, then:
    type 'stop' to stop this link
    type '..' to cancel
    or type text to send to the link"""
        try:
            idx = int(args[0:])
            print(idx)
        except ValueError:
            idx = -1
        if -1 < idx < len(self.links):
            link = self.links[idx]
            link_members = linkmembers(self.nodes, link)
            message = str(input("%s(%s) %s>" % (link, len(link_members), link_members)))
            if message == "stop":
                link.stop()
            elif message == "start":
                link.start()
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
             
    def do_all(self, args):
        """show available nodes with links"""
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
    
    
    GET_COMMANDS = ['link', 'neighbors']
    
    def do_get(self, args):
        '''type "get neighbors n0" to get paths to all nodes from n0 using Dijkstra algorithm
or type "get links n0 n1" to get all links between n0 and n1'''
        args = self.parseline(args)
        if args[0] == 'neighbors':
            try:
                weight, path = self.get_neighbors(args[1])
                for i in weight:
                    print('[{0}] to {1}: {2}, total {3} hops'.format(args[1], i, path[i], weight[i]))
            except:
                print('something wrong')
        elif args[0] == 'link':
            self.get_link(args[1])
        else:
            print('???')
            
    def complete_get(self, text, line, begidx, endidx):
        if not text:
            compl = self.GET_COMMANDS[:]
        else:
            compl = [ f for f in self.GET_COMMANDS if f.startswith(text)]
        return compl
          
    def default(self, line):
        if line[0] == 'n':
            self.do_n(line[1:])
        elif line[0] == 'l':
            self.do_l(line[1:])
        else:
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
        
    def get_neighbors(self, args):
        start_node = self.get_node(args)
        if start_node:
            wieght, path = dijkstra(self.nodes, start_node)
            return wieght, path
        else:
            print("'{0}' is not a node!".format(args))
            
    def get_link(self, args):
        args = self.parseline(args)
        try:
            node0 = int(args[0][1:])
            node1 = int(args[1][1:])
            if node0 != node1 and -1 < node0 < len(self.nodes) and -1 < node1 < len(self.nodes):
                node0 = self.nodes[node0]
                node1 = self.nodes[node1]
                print('link = ', get_cummon_link(node0, node1))
            elif node0 == node1:
                print('same node')
            elif -1 < node0 < len(self.nodes):
                print('n%s is not a node!' % node1)
            elif -1 < node1 < len(self.nodes):
                print('n%s is not a node!' % node0)
            else:
                print('error1')
        except:
            print('type:\n\tget link n0 n1')    
            
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
