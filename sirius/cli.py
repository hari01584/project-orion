import os
import sys
import platform
import argparse
import subprocess
import configparser
import socket

IS_DEBUG = False
def log(level, message):
    if(IS_DEBUG or level.lower() == 'fatal' or level.lower() == 'out'):
        print('[%s] %s'%(level, message))

config = configparser.ConfigParser()
config.read('server.ini')

try:
    SERVER_HOST = config['Server']['host']
    SERVER_PORT = config['Server']['port']
    SERVER_TOKEN = config['Server']['token']
except Exception:
    log("fatal", "server.ini corrupt or not found.")
    exit(-1)

def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def resolveHostname(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """
    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'
    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]
    proc = subprocess.check_output(command)

    ipv = find_between(str(proc), 'Reply from ', ': time<1ms')
    log('trace', 'ip resolved address is %s'%(ipv,))
    log('trace', 'packet data: %s'%(proc,))

    return (proc)

def c_verify_server_ping():
    log("trace", "verifying valid server connection")
    try:
        resolveHostname(SERVER_HOST)
    except subprocess.CalledProcessError as e:
        log('fatal', "Host server offline or unavaliable. Try switching wifi channel using windows app NetSetMan or linux command nmcli")
        exit(-1)
    log('out', "Host server online.. Starting CLI.")
    
parser = argparse.ArgumentParser(prog='cli.py')
parser.add_argument('--debug', action='store_true')

sp = parser.add_subparsers(dest='cmd')

expose_parser = sp.add_parser('expose')
expose_parser.add_argument('-t','--tcp', nargs='+', help='<Required> Set flag', type=int, required=False)
expose_parser.add_argument('-u','--udp', nargs='+', help='<Required> Set flag', type=int, required=False)

connect_parser = sp.add_parser('connect')
connect_parser.add_argument('port', type=int)

sp.add_parser('status')

args = parser.parse_args(sys.argv[1:])

IS_DEBUG = args.debug
c_verify_server_ping()

if(args.cmd == 'expose'):
    # EXPOSE COMMANDS
    if(args.tcp is not None):
        for p in args.tcp:
            print(p)
elif(args.cmd == 'connect'):
    # connect COMMANDS
    pass
