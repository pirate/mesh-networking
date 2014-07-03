import pickle
import socket
import threading

# We'll pickle a list of numbers:
someList = [ 1, 2, 7, 9, 0 ]
pickledList = pickle.dumps ( someList )

# Our thread class:
class ClientThread ( threading.Thread ):

   # Override Thread's __init__ method to accept the parameters needed:
   def __init__ ( self, channel, details ):

      self.channel = channel
      self.details = details
      threading.Thread.__init__ ( self )

   def run ( self ):

      print 'Received connection:', self.details [ 0 ]
      self.channel.send ( pickledList )
      for x in xrange ( 10 ):
         print self.channel.recv ( 1024 )
      self.channel.close()
      print 'Closed connection:', self.details [ 0 ]

# Set up the server:
server = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
server.bind ( ( 'localhost', 2727 ) )
server.listen ( 5 )

# Have the server serve "forever":
while True:
   channel, details = server.accept()
   ClientThread ( channel, details ).start()
