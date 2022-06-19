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
import cmd
import sys
import os
import re

class cl_interface(cmd.Cmd):
    def __init__(self, args):
        self.args = args
        cmd.Cmd.__init__(self)
        self.prompt = "tftp client> "
        cmd.Cmd.doc_header = None
        self.call = "cl_interface"
    
    def default(self, line):
        self.stdout.write("Unknown command: %s\n" % (line.split()[0],))    

    def do_get(self, addarg):
        'get command: download files from server\nusage: get (<source_file>) [<dest_file>]'
        self.args["get"] = True
        if len(addarg.split()) == 1:
            self.args["<source_file>"] = addarg
            self.args["<dest_file>"] = addarg
        elif len(addarg.split()) == 2: 
            self.args["<source_file>"], self.args["<dest_file>"]= addarg.split()
        else: 
            print("Usage: get remotefile [localfile]")
            return
        action(self.args, self.call)
        
    def do_put(self, addarg):
        'put command: upload files to server\nusage: put (<source_file>) [<dest_file>]'
        self.args["put"] = True
        if len(addarg.split()) == 1:
            self.args["<source_file>"] = addarg
            self.args["<dest_file>"] = addarg
        elif len(addarg.split()) == 2: 
            self.args["<source_file>"], self.args["<dest_file>"]= addarg.split()
        else: 
            raise ValueError(f"get command only allows one or two arguments.")
        action(self.args, self.call)

    def do_dir(self, *args):
        'dir command: list server files'
        self.args["get"] = True     
        self.args["<source_file>"] = ''
        self.args["<dest_file>"] = ''
        action(self.args, self.call)
    
    def do_help(self, *args):
        print ('''Commands:
    get remote_file [local_file] - get a file from server and save it as local_file\n\
    put local_file [remote_file] - send a file to server and store it as remote_file\n\
    dir                          - obtain a listing of remote files
    quit                         - exit TFTP client''')

    def do_quit(self, arg):
        print("Exiting TFTP client.\nGoodbye!")
        sys.exit(1)

    def help_quit(self):
        print ("syntax: quit"),
        print ("-- terminates the application")


def action(args, call):
    if args.get('<source_file>'):
        aval_dest = re.search("\.$|/$", args.get('<dest_file>')) 
        aval_source = (re.search("\.$|/$", args.get('<source_file>')))
        if aval_dest and aval_source:
            print("Source and destination are directories")
            return
        elif aval_dest or aval_source:
            print("Is a directory")
            return
    try:    
        if args.get("get"):
            tot_bytes = tftp.get_file((args.get('<server>')[0],int(args.get("-p"))),args.get('<source_file>'), args.get('<dest_file>'), args.get('<server>')[1])
            if args.get('<source_file>') == args.get('<dest_file>'):
                print(f"Received file '{args.get('<source_file>')}' {tot_bytes} bytes.")
            else:
                print(f"Received file '{args.get('<source_file>')}' {tot_bytes} bytes.\nSaved locally as '{args.get('<dest_file>')}'")

        elif args.get("put"):
            if not "/" in args.get('<dest_file>'):
                tot_bytes = tftp.put_file((args.get('<server>')[0],int(args.get("-p"))),args.get('<source_file>'), args.get('<dest_file>'))
            else:
                args['<dest_file>'] = args.get('<dest_file>').split('/')[-1]
                tot_bytes = tftp.put_file((args.get('<server>')[0],int(args.get("-p"))),args.get('<source_file>'), args.get('<dest_file>'))
            if args.get('<source_file>') == args.get('<dest_file>') or args.get('<source_file>').split('/')[-1] == args.get('<dest_file>'):
                print(f"Sent file '{args.get('<source_file>')}' {tot_bytes} bytes.")
            else:
                print(f"Sent file '{args.get('<source_file>')}' {tot_bytes} bytes.\nSaved remotely as '{args.get('<dest_file>')}'")
    except tftp.ProtocolError as err: # wrong block number 
        print(err)
        os.remove(args.get('<dest_file>')) 
    except tftp.NetworkError as err:
        if call == "cl_interface":
            os.remove(args.get('<dest_file>'))
            print("Server not responding. Exiting.")
            sys.exit()
        else: 
            print(err)
            os.remove(args.get('<dest_file>')) 
    except ValueError as err: #not ascii error
        print(err)
        os.remove(args.get('<dest_file>')) 
    except tftp.Err as err: #server errors. ex: file not found
        print(err)
        os.remove(args.get('<dest_file>')) 
    #except IsADirectoryError as err:
        #aval_dest = re.search("\.$|/$", args.get('<dest_file>')) 
        #aval_source = (re.search("\.$|/$", args.get('<source_file>')))
        #if aval_dest and aval_source:
        #    print("Source and destination are directories")
        #else:
        #    print("Is a directory")
    

#def tftp_interactive(args, server_info):    
#    if server_info[1]:
#        print(f"Exchaging files with server '{server_info[1]}' ({server_info[0]})")
#        print("not yet implemented")
#    else:
#        print(f"Exchaging files with server {server_info[0]}")
#        print("not yet implemented")
#    start_cli = cl_interface(args, server_info)
#    start_cli.cmdloop()

def verify_cli_in(args):  
    try:
        args['<server>'] = tftp.get_server_info(args['<server>'])
    except ValueError as err:
        print(err)
        exit()
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
        if not(args.get("put") or args.get("get")) and not args.get("<source_file>"):             #not efficient: if there's a firewall denying ICMP requests,
            ping = os.popen(f"ping -c4 {args.get('<server>')[0]} &> /dev/null; echo $?").read()   #the program will be terminated. Solution: use GET command
            ind = ping.index("% packet loss")                                                     #with specific filename (like DIR)
            packet_loss = int(ping[ind-2:ind])
            if not packet_loss == 0:
                if args.get('<server>')[1]:
                    print(f"Error reaching the server '{args.get('<server>')[1]}' ({args.get('<server>')[0]})")
                else:
                    print(f"Error reaching the server '{args.get('<server>')[0]}")
                sys.exit()
            else:
                call = "cl_interface" 
                action(args, call)
                start_cli = cl_interface(args)
                if args.get('<server>')[1]:
                    start_cli.cmdloop(intro = f"Exchaging files with server '{args.get('<server>')[1]}' ({args.get('<server>')[0]})")
                else:
                    start_cli.cmdloop(intro = f"Exchaging files with server '{args.get('<server>')[0]}'")
                return args['<server>']

args=docopt.docopt(__doc__)

server_info = verify_cli_in(args)

call = "non_intercative"
action(args, call)