"""
tftpy module - defines common functions to handle data and packets of a TFTP client and a TFTP server.



Developed by:
    João Sitole
    Rui Caria

2022/07/01
"""

# pylint: disable=redefined-outer-name

from hashlib import new
from http import client
from pydoc import cli
import re
import struct 
import string
import ipaddress
import socket 
from typing import Tuple
import os
import random
################################################################################
##
##      PROTOCOL CONSTANTS AND TYPES
##
################################################################################

MAX_DATA_LEN = 512            # bytes
INACTIVITY_TIMEOUT = 30       # segs
MAX_BLOCK_NUMBER = 2**16 - 1 
DEFAULT_MODE = 'octet'
SOCKET_BUFFER_SIZE = 8192     # bytes


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
    UNDEF_ERROR        : 'Undefined error.',
    FILE_NOT_FOUND     : 'File not found.',
    ACCESS_VIOLATION   : 'Access violation.',
    DISK_FULL_ALLOC_EXCEEDED : 'Disk full or allocation exceeded.',
    ILLEGAL_OPERATION   : 'Illegal TFTP operation.',
    UNKNOWN_TRANSFER_ID : 'Unknown transfer ID.',
    FILE_EXISTS         : 'File already exists.',
    NO_SUCH_USER        : 'No such user.'
}

INET4Address = Tuple[str, int]        # TCP/UDP address => IPv4 and port
# FileReference = Union[str, BinaryIO]  # A path or a file object

###############################################################
##
##      SEND AND RECEIVE MESSAGES
##
###############################################################

def get_file(serv_addr: INET4Address, file_name: str, new_file_name: str, serv_name):
    """
    RRQ a file given by filename from a remote TFTP server given
    by serv_addr.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        with open(new_file_name, 'wb') as file:
            sock.settimeout(INACTIVITY_TIMEOUT)
            rrq = pack_rrq(file_name)
            try:
                sock.sendto(rrq, serv_addr)
            except:
                raise NetworkError(f"Error reaching the server '{serv_name}' ({serv_addr[0]}).")           
            next_block_num = 1
            tot_data = 0
            while True:
                packet, new_serv_addr = sock.recvfrom(SOCKET_BUFFER_SIZE)
                opcode = unpack_opcode(packet)
                    
                if opcode == DAT:
                    block_num, data = unpack_dat(packet)
                    if block_num != next_block_num:
                        raise ProtocolError(f"Invalid block number {block_num}")

                    file.write(data)
                    tot_data += len(data)

                    ack = pack_ack(next_block_num)
                    sock.sendto(ack, new_serv_addr)

                    if len(data) < MAX_DATA_LEN:
                        break

                elif opcode == ERR:
                    raise Err(*unpack_err(packet))

                else: # opcode not in (DAT, ERR):
                    raise ProtocolError(f'Invalid opcode {opcode}')

                next_block_num += 1
            return tot_data
        #:
    #:
#:

##################################################################################
def dir_req(serv_addr: INET4Address):
    """
    RRQ a file given by filename from a remote TFTP server given
    by serv_addr.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(INACTIVITY_TIMEOUT)
        rrq = pack_rrq("")
        file = b""
        try:
            sock.sendto(rrq, serv_addr)
        except:
            raise NetworkError(f"Error reaching the server {serv_addr[0]}'.")           
        next_block_num = 1
        tot_data = 0
        while True:
            packet, new_serv_addr = sock.recvfrom(SOCKET_BUFFER_SIZE)
            opcode = unpack_opcode(packet)
                
            if opcode == DAT:
                block_num, data = unpack_dat(packet)
                if block_num != next_block_num:
                    raise ProtocolError(f"Invalid block number {block_num}")
                file += data
                tot_data += len(data)
                ack = pack_ack(next_block_num)
                sock.sendto(ack, new_serv_addr)
                if len(data) < MAX_DATA_LEN:
                    break
            elif opcode == ERR:
                raise Err(*unpack_err(packet))
            else: # opcode not in (DAT, ERR):
                raise ProtocolError(f'Invalid opcode {opcode}')
            next_block_num += 1
        print(file.decode())
        return tot_data
        #:
    #:
#:
###################################################################################################
def iter_bytes(my_bytes):
    for i in range(len(my_bytes)):
        yield my_bytes[i:i+1]

def put_file(serv_addr: INET4Address, file_name: str, new_file_name: str, serv_name='' ):
    """
    WRQ a file given by filename to a remote TFTP server given
    by serv_addr.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        with open(file_name, 'rb') as file:
            sock.settimeout(INACTIVITY_TIMEOUT)
            wrq = pack_wrq(new_file_name)
            try:
                sock.sendto(wrq, serv_addr)
            except:
                raise NetworkError(f"Error reaching the server '{serv_name}' ({serv_addr[0]}).")           
            next_block_num = 1
            read_file = file.read()
            iter_file_cont = iter_bytes(read_file)    
            _supra_state_ = 1
            tot_data = 0
            while _supra_state_ == 1:
                packet, new_serv_addr = sock.recvfrom(SOCKET_BUFFER_SIZE)
                opcode = unpack_opcode(packet)
                
                if opcode == ACK:
                    block_num = unpack_ack(packet)
                    if block_num + 1 != next_block_num:
                        raise ProtocolError(f'Invalid block number {block_num}')

                    _sub_state_ = 1
                    data = b''
                    while _sub_state_ == 1:
                        try:
                            if len(data) < 512:
                                w = next(iter_file_cont)
                                data += w
                                tot_data += 1

                            else:
                                dat = pack_dat(next_block_num, data)
                                sock.sendto(dat, new_serv_addr)
                                _sub_state_= 0
                       
                        except StopIteration:
                            dat = pack_dat(next_block_num, data)
                            sock.sendto(dat, new_serv_addr)
                            _sub_state_= 0
                            _supra_state_= 0
                                                  
                    
                next_block_num += 1
            return tot_data

######################################################################################################
def get_resp(client_addr, file_name):
    """
    RRQ request server response.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((client_addr[0],random.randrange(49152,65535)))
        with open(file_name, 'rb') as file:
            sock.settimeout(INACTIVITY_TIMEOUT)
            next_block_num = 1
            read_file = file.read()
            iter_file_cont = iter_bytes(read_file)    
            data = b''
            tot_data = 0
            _supra_state_ = 2
            while _supra_state_ == 2:
                try:
                    if len(data) < 512:
                        w = next(iter_file_cont)
                        data += w
                        tot_data += 1
                    else:
                        dat = pack_dat(next_block_num, data)
                        sock.sendto(dat, client_addr)
                        _sub_state_= 1
                        _supra_state_ = 1
                except StopIteration:
                    dat = pack_dat(next_block_num, data)
                    sock.sendto(dat, client_addr)
                    _sub_state_= 1
                    _supra_state_= 1
            next_block_num += 1
            while _supra_state_ == 1:
                packet, client_addr = sock.recvfrom(SOCKET_BUFFER_SIZE)
                opcode = unpack_opcode(packet)
                if opcode == ACK:
                    block_num = unpack_ack(packet)
                    if block_num + 1 != next_block_num:
                        raise ProtocolError(f'Invalid block number {block_num}')
                    _sub_state_ = 1
                    data = b''
                    while _sub_state_ == 1:
                        try:
                            if len(data) < 512:
                                w = next(iter_file_cont)
                                data += w
                                tot_data += 1
                            else:
                                dat = pack_dat(next_block_num, data)
                                sock.sendto(dat, client_addr)
                                _sub_state_= 0
                        except StopIteration:
                            dat = pack_dat(next_block_num, data)
                            sock.sendto(dat, client_addr)
                            _sub_state_= 0
                            _supra_state_= 0
                next_block_num += 1
            print(f"'{file_name}': file sent")
            return tot_data

######################################################################################################
def dir_resp(client_addr, file_name):
    """
    DIR request server response.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((client_addr[0],random.randrange(49152,65535)))
        file = os.popen(f"ls -l").read().encode()
        print(file)
        sock.settimeout(INACTIVITY_TIMEOUT)
        next_block_num = 1
        iter_file_cont = iter_bytes(file)    
        data = b''
        tot_data = 0
        _supra_state_ = 2
        while _supra_state_ == 2:
            try:
                if len(data) < 512:
                    w = next(iter_file_cont)
                    data += w
                    tot_data += 1
                else:
                    dat = pack_dat(next_block_num, data)
                    sock.sendto(dat, client_addr)
                    _sub_state_= 1
                    _supra_state_ = 1
            except StopIteration:
                dat = pack_dat(next_block_num, data)
                sock.sendto(dat, client_addr)
                _sub_state_= 1
                _supra_state_= 1
        next_block_num += 1
        while _supra_state_ == 1:
            packet, client_addr = sock.recvfrom(SOCKET_BUFFER_SIZE)
            opcode = unpack_opcode(packet)
            if opcode == ACK:
                block_num = unpack_ack(packet)
                if block_num + 1 != next_block_num:
                    raise ProtocolError(f'Invalid block number {block_num}')
                _sub_state_ = 1
                data = b''
                while _sub_state_ == 1:
                    try:
                        if len(data) < 512:
                            w = next(iter_file_cont)
                            data += w
                            tot_data += 1
                        else:
                            dat = pack_dat(next_block_num, data)
                            sock.sendto(dat, client_addr)
                            _sub_state_= 0
                    except StopIteration:
                        dat = pack_dat(next_block_num, data)
                        sock.sendto(dat, client_addr)
                        _sub_state_= 0
                        _supra_state_= 0
            next_block_num += 1
        print(f"'{file_name}': file sent")
        return tot_data#####################################################################################################################
################################################################################
##
##      PACKET PACKING AND UNPACKING
##
################################################################################

def pack_rrq(filename: str, mode: str = DEFAULT_MODE) -> bytes:
    return _pack_rq(RRQ, filename, mode)
#:

def unpack_rrq(packet: bytes) -> Tuple[str, str]:
    return _unpack_rq(packet)
#:

def pack_wrq(filename: str, mode: str = DEFAULT_MODE) -> bytes:
    return _pack_rq(WRQ, filename, mode)
#:

def unpack_wrq(packet: bytes) -> Tuple[str, str]:
    return _unpack_rq(packet)
#:

def _pack_rq(opcode: int, filename: str, mode: str = DEFAULT_MODE) -> bytes:
    if not is_ascii_printable(filename):
        raise ValueError(f"Invalid filename '{filename}' (not ascii printable).")
    if mode != 'octet':
        raise ValueError(f'Invalid mode {mode}. Supported modes: octet.')

    pack_filename = filename.encode() + b'\x00'
    pack_mode = mode.encode() + b'\x00'
    pack_format = f'!H{len(pack_filename)}s{len(pack_mode)}s'
    return struct.pack(pack_format, opcode, pack_filename, pack_mode)
#:

def _unpack_rq(packet: bytes) -> Tuple[str, str]:
    filename_delim = packet.index(b'\x00', 2)
    filename = packet[2:filename_delim].decode()
    if not is_ascii_printable(filename):
        raise ValueError(f"Invalid filename '{filename}'' (not ascii printable).")

    mode_delim = len(packet) - 1
    mode = packet[filename_delim + 1:mode_delim].decode()

    return (filename, mode)
#:

def pack_dat(block_number: int, data: bytes) -> bytes:
    if not 0 <= block_number <= MAX_BLOCK_NUMBER:
        ValueError(f'Invalid block number {block_number}')
    if len(data) > MAX_DATA_LEN:
        ValueError(f'Invalid data length {len(data)} ')
    fmt = f'!HH{len(data)}s'
    return struct.pack(fmt, DAT, block_number, data)
#:

def unpack_dat(packet: bytes) -> Tuple[int, bytes]:
    _, block_number = struct.unpack('!HH', packet[:4])
    return block_number, packet[4:]
#:

def pack_ack(block_number: int) -> bytes:
    if not 0 <= block_number <= MAX_BLOCK_NUMBER:
        ValueError(f'Invalid block number {block_number}')
    return struct.pack('!HH', ACK, block_number)
#:

def unpack_ack(packet: bytes) -> int:
    if len(packet) > 4:
        raise ValueError(f'Invalid packet length: {len(packet)}')
    return struct.unpack('!H', packet[2:4])[0]
#:

def unpack_opcode(packet: bytes) -> int:
    opcode, *_ = struct.unpack("!H", packet[:2])
    if opcode not in (RRQ, WRQ, DAT, ACK, ERR):
        raise ValueError(f'Unrecognized opcode {opcode}.')
    return opcode
#:

def unpack_err(packet: bytes) -> Tuple[int, str]:
    _, error_num, error_msg = struct.unpack(f'!HH{len(packet)-4}s', packet)
    return error_num, error_msg[:-1]
#:

################################################################################
##
##      ERRORS AND EXCEPTIONS
##
################################################################################

class NetworkError(Exception):
    """
    Any network error, like "host not found", timeouts, etc.
    """
#:

class ProtocolError(NetworkError):
    """
    A protocol error like unexpected or invalid opcode, wrong block 
    number, or any other invalid protocol parameter.
    """
#:

class Err(Exception):
    """
    An error sent by the server. It may be caused because a read/write 
    can't be processed. Read and write errors during file transmission 
    also cause this message to be sent, and transmission is then 
    terminated. The error number gives a numeric error code, followed 
    by an ASCII error message that might contain additional, operating 
    system specific information.
    """
    def __init__(self, error_code: int, error_msg: bytes):
        super().__init__(f'TFTP Error {error_code}')
        self.error_code = error_code
        self.error_msg = error_msg.decode()     
    
    def __str__(self):
        return "{}".format(self.error_msg+".")
    #:
#:

################################################################################
##
##      COMMON UTILITIES
##      Mostly related to network tasks
##
################################################################################

def _make_is_valid_hostname():
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    def _is_valid_hostname(hostname):
        """
        From: http://stackoverflow.com/questions/2532053/validate-a-hostname-string
        See also: https://en.wikipedia.org/wiki/Hostname (and the RFC 
        referenced there)
        """
        if len(hostname) > 255:
            return False
        if hostname[-1] == ".":
            # strip exactly one dot from the right, if present
            hostname = hostname[:-1]
        return all(allowed.match(x) for x in hostname.split("."))
    return _is_valid_hostname
#:
is_valid_hostname = _make_is_valid_hostname()


def get_server_info(server_addr: str) -> Tuple[str, str]:
    """
    Returns the server ip and hostname for server_addr. This param may
    either be an IP address, in which case this function tries to query
    its hostname, or vice-versa.
    This functions raises a ValueError exception if the host name in
    server_addr is ill-formed, and raises NetworkError if we can't get
    an IP address for that host name.
    TODO: refactor code...
    """
    try:
        ipaddress.ip_address(server_addr)
    except ValueError:
        # server_addr not a valid ip address, then it might be a 
        # valid hostname
        # pylint: disable=raise-missing-from
        if not is_valid_hostname(server_addr):     
            raise ValueError(f"Invalid hostname: {server_addr}.")
        server_name = server_addr
        try:
            # gethostbyname_ex returns the following tuple: 
            # (hostname, aliaslist, ipaddrlist)
            server_ip = socket.gethostbyname_ex(server_name)[2][0]
        except socket.gaierror:
            raise ValueError(f"Unknown server: {server_name}.")
    else:  
        # server_addr is a valid ip address, get the hostname
        # if possible
        server_ip = server_addr
        try:
            # returns a tuple like gethostbyname_ex
            server_name = socket.gethostbyaddr(server_ip)[0]
        except socket.herror:
            server_name = ''
    return server_ip, server_name
#:

def is_ascii_printable(txt: str) -> bool:
    return not set(txt) - set(string.printable)
    # ALTERNATIVA: return set(txt).issubset(string.printable)
#:

if __name__ == '__main__':
    print()
    print("____ RRQ ____")
    rrq = pack_rrq('relatorio.pdf')
    print(rrq)
    filename, mode = unpack_rrq(rrq)
    print(f"Filename: {filename} Mode: {mode}")

    print()
    print("____ WRQ ____")
    wrq = pack_wrq('relatorio.pdf')
    print(wrq)
    filename, mode = unpack_wrq(wrq)
    print(f"Filename: {filename} Mode: {mode}")

#: