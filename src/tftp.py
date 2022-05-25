"""
This module handles all TFTP related data structures and 
methods.

(C) João Galamba, 2022
"""
# pylint: disable=redefined-outer-name

from multiprocessing.sharedctypes import Value
import struct 
import string
from socket import socket, AF_INET, SOCK_DGRAM
from typing import Tuple

################################################################################
##
##      PROTOCOL CONSTANTS AND TYPES
##
################################################################################

MAX_DATA_LEN = 512            # bytes
INACTIVITY_TIMEOUT = 30       # segs
MAX_BLOCK_NUMBER = 2**16 - 1 
DEFAULT_MODE = 'octet'

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

# INET4Address = Tuple[str, int]        # TCP/UDP address => IPv4 and port
# FileReference = Union[str, BinaryIO]  # A path or a file object

def pack_rrq(filename: str, mode: str = DEFAULT_MODE) -> bytes:
    return _pack_rrq_wrq(RRQ, filename, mode)
#:

def unpack_rrq(packet: bytes) -> Tuple[str, str]:
    return _unpack_rrq_wrq(RRQ, packet)
#:

def pack_wrq(filename: str, mode: str = DEFAULT_MODE) -> bytes:
    return _pack_rrq_wrq(WRQ, filename, mode)
#:

def unpack_wrq(packet: bytes) -> Tuple[str, str]:
    return _unpack_rrq_wrq(WRQ, packet)
#:

def _pack_rrq_wrq(opcode: int, filename: str, mode: str = DEFAULT_MODE) -> bytes:
    if not is_ascii_printable(filename):
        raise ValueError(f'Invalid filename {filename} (not ascii printable)')
    if mode != 'octet':
        raise ValueError(f'Invalid mode {mode}. Supported modes: octet.')

    pack_filename = filename.encode() + b'\x00'
    pack_mode = mode.encode() + b'\x00'
    pack_format = f'!H{len(pack_filename)}s{len(pack_mode)}s'
    return struct.pack(pack_format, opcode, pack_filename, pack_mode)
#:

def _unpack_rrq_wrq(opcode: int, packet: bytes) -> Tuple[str, str]:
    filename_delim = packet.index(b'\x00', 2)
    filename = packet[2:filename_delim].decode()
    if not is_ascii_printable(filename):
        raise ValueError(f'Invalid filename {filename} (not ascii printable).')

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
    opcode, block_number = struct.unpack('!HH', packet[:4])
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

def is_ascii_printable(txt: str) -> bool:
    return not set(txt) - set(string.printable)
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
