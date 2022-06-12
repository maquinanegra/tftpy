'''
TFTPy - This module implements an interactive and command line TFTP 
client.

Usage: 
  client.py (get|put) [-p serv_port] <server> <source_file> [<dest_file>]
  client.py [-p serv_port] <server>  

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

def action(args,server_info):
    if args.get("get"):
        print("NEW FILE\n",args.get('<dest_file>'))
        tftp.get_file((server_info[0],int(args.get("-p"))),args.get('<source_file>'), args.get('<dest_file>'))

def tftp_interactive(args, server_info):
    if server_info[1]:
        print(f"Exchaging files with server '{server_info[1]}' ({server_info[0]})")
        print("not yet implemented")
    else:
        print(f"Exchaging files with server {server_info[0]}")
        print("not yet implemented")

def verify_cli_in(args):    
    _server_info = tftp.get_server_info(args['<server>'])
    # specified port is not a number > exit 
    if not args["-p"].isnumeric():
        raise docopt.DocoptExit
    # mandatory fields > not verified    
    if (not args.get("<source_file>") and (args.get("put")==True or args.get("get")==True)) or (args.get("<source_file>") and (args.get("put")==False and args.get("get")==False)):
        raise docopt.DocoptExit
    else:
        # no destination file specified > use source filename
        if not args.get("<dest_file>"): 
            args["<dest_file>"]=args["<source_file>"]
        # interactive cli access
        if not(args.get("put") or args.get("get")) and not args.get("<source_file>"):
            tftp_interactive(args, server_info)
    return _server_info

args=docopt.docopt(__doc__)
print("ARGS\n",args)

server_info = verify_cli_in(args)
print("SERVER INFO\n",server_info)

action(args,server_info)

