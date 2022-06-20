
# from socket import socket, AF_INET, SOCK_DGRAM
# import time
# def time_server(address):
#    sock = socket(AF_INET, SOCK_DGRAM)
#    sock.bind(address)
#    while True:
#        msg, addr = sock.recvfrom(8192)
#        print('Got message from', addr)
#        resp = time.ctime()
#        sock.sendto(resp.encode('ascii'), addr)

# if __name__ == '__main__':
#    time_server(('', 20000))
##########################################################

# from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
# import time

# def time_server(address):
#    sock = socket(AF_INET, SOCK_DGRAM)
#    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
#    sock.bind(address)
#    while True:
#        msg, addr = sock.recvfrom(8192)
#        print('Got message from', addr)
#        resp = time.ctime()
#        sock.sendto(resp.encode(), addr)

# if __name__ == '__main__':
#    time_server(('', 20001))

#########################################################

# TFTP message opcodes
RRQ = 1   # Read Request
WRQ = 2   # Write Request
DAT = 3   # Data transfer
ACK = 4   # Acknowledge DAT
ERR = 5   # Error packet; what the server responds if a read/write 
          # can't be processed, read and write errors during file 
          # transmission also cause this message to be sent, and 
          # transmission is then terminated. The error number gives a 
          # numeric error code, followed by an ASCII error message that
          # might contain additional, operating system specific 
          # information.

# TFTP standard error codes and messages
UNDEF_ERROR              = 0
FILE_NOT_FOUND           = 1
ACCESS_VIOLATION         = 2
DISK_FULL_ALLOC_EXCEEDED = 3
ILLEGAL_OPERATION        = 4
UNKNOWN_TRANSFER_ID      = 5
FILE_EXISTS              = 6
NO_SUCH_USER             = 7

ERROR_MSGS = {
    UNDEF_ERROR             : 'Undefined error.',
    FILE_NOT_FOUND          : 'File not found.',
    ACCESS_VIOLATION        : 'Access violation.',
    DISK_FULL_ALLOC_EXCEEDED: 'Disk full or allocation exceeded.',
    ILLEGAL_OPERATION       : 'Illegal TFTP operation.',
    UNKNOWN_TRANSFER_ID     : 'Unknown transfer ID.',
    FILE_EXISTS             : 'File already exists.',
    NO_SUCH_USER            : 'No such user.'
}

from socketserver import BaseRequestHandler, ThreadingUDPServer
from socket import socket, AF_INET, SOCK_DGRAM
import time

class TimeHandler(BaseRequestHandler):
    def handle(self):
        # Get message and client socket
        msg = self.request[0]
        print('Got request', msg, 'from', self.client_address)
        resp = time.ctime()
        
        # Create another socket with an ephemeral port for the reply
        with socket(AF_INET, SOCK_DGRAM) as sock:
            sock.sendto(resp.encode(), self.client_address)

if __name__ == '__main__':
    # Threading server allows serving multiple requests concurrently
    ThreadingUDPServer.allow_reuse_address = True
    serv = ThreadingUDPServer(('localhost', 20022), TimeHandler)
    print('Starting server...', serv)
    serv.serve_forever()

