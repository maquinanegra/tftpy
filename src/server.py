from socketserver import ThreadingUDPServer, DatagramRequestHandler
from threading import Thread
import tftp
import os

N_CONN = 16

class PacketHandler(DatagramRequestHandler):
    def handle(self):
        print('Connection:', self.client_address)
        # Get message and client socket
        packet, sock = self.request
        opcode = tftp.unpack_opcode(packet)
        file_name, mode = tftp.unpack_rrq(packet)

        if opcode == 1:
            if file_name != '':        
                tftp.get_resp(self.client_address, file_name)
            else:
                print("************DIR************")
                tftp.dir_resp(self.client_address, file_name)
                #data = os.popen(f"ls -l").read().encode()
                #if file_name != 'dir':
                
if __name__ == '__main__':
    serv = ThreadingUDPServer(('', 69), PacketHandler)
    for n in range(N_CONN):
        t = Thread(target=serv.serve_forever)
        t.daemon = True
        t.start()
    serv.serve_forever()
