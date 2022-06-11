'''
TFTPy - This module implements an interactive and command line TFTP 
client.

Usage: 
  client.py [get|put] [-p serv_port] <server> [<source_file> [<dest_file>]]

Options: 
-h --help       show help
get             get file from server
put             send file to server
-p serv_port    [default: 69] specify a communication port
server          server IP or name
source_file     name of the source file
dest_file       name for the destination file


'''

from click import UsageError
import docopt
import sys

args=docopt.docopt(__doc__)
print(args)


# specified por is not a number -> exit 
if not args["-p"].isnumeric():
    raise docopt.DocoptExit
else:
    if not args.get("<source_file>"): # no source file specified -> interactive
        comm = input("tftp client>")    
    if not args.get("<dest_file>"): # no destination file specified -> use source filename
        args["<dest_file = args>"]=args["<source_file>"]


