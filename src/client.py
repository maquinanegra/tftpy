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

import docopt
import tftp


def tftp_interactive(args, server_info):
    print(f"Exchaging files with server '{server_info[1]}' ({server_info[0]})")
    intera_comm = input("tftp client>")


def verify_cli_in(args):    
    # specified port is not a number > exit 
    if not args["-p"].isnumeric():
        raise docopt.DocoptExit
    else:
        server_info = tftp.get_server_info(args['<server>'])
        # no destination file specified > use source filename
        if not args.get("<dest_file>"): 
            args["<dest_file = args>"]=args["<source_file>"]
        # mandatory fields > not verified    
        if (not args.get("<source_file>") and (args.get("put")==True or args.get("get")==True)) or (args.get("<source_file>") and (args.get("put")==False and args.get("get")==False)):
            raise docopt.DocoptExit
        # interactive cli access
    
        else: 
            tftp_interactive(args, server_info)

args=docopt.docopt(__doc__)
#print(args)

verify_cli_in(args)


