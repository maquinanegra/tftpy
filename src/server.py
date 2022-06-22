from socketserver import ThreadingUDPServer, DatagramRequestHandler
from threading import Thread
    
import time

class TimeHandler(DatagramRequestHandler):
    def handle(self):
        print('Connection:', self.client_address)
        # Get message and client socket
        msg, sock = self.request
        resp = time.ctime()
        sock.sendto(resp.encode('ascii'), self.client_address)
if __name__ == '__main__':
    NWORKERS = 16
    serv = ThreadingUDPServer(('', 20000), TimeHandler)
    for n in range(NWORKERS):
        t = Thread(target=serv.serve_forever)
        t.daemon = True
        t.start()
    serv.serve_forever()