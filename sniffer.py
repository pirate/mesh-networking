import socket

# the public network interface
HOST = socket.gethostbyname(socket.gethostname())

print HOST

# create a raw socket and bind it to the public interface
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
s.bind((HOST, 100))

# Include IP headers
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# receive all packages
#s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

for _ in range(10000):
    print s.recvfrom(100)
