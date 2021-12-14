import os
import sys
import platform
import argparse
import subprocess
import configparser
import socket
import random

IS_DEBUG = False
def log(level, message):
    if(IS_DEBUG or level.lower() in ['fatal', 'out', 'check', 'success']):
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

    ipv = find_between(str(proc), 'Reply from ', '%')
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

    log('check', "host server online.")

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

def hard_clone_section(cp, section_from, section_to):
    items = cp.items(section_from)
    cp.add_section(section_to)
    for item in items:
        cp.set(section_to, item[0], item[1])

def rename_section(cp, section_from, section_to):
    hard_clone_section(cp, section_from, section_to)
    cp.remove_section(section_from)

def expose(tcps, udps):
    # Write configs
    config = configparser.ConfigParser()
    config.read('t_configs/template_client.ini')

    config.set('common', 'server_addr', SERVER_HOST)
    config.set('common', 'server_port', SERVER_PORT)
    config.set('common', 'token', SERVER_TOKEN)

    port = random.randint(8000,65535)
    log('success', 'Your pairing port is %s'%(port,))
    nl = 'link_'+str(port)
    rename_section(config, 'link_', nl)

    if(tcps is not None):
        ns = 'p2p_tcp_'+str(port)
        rename_section(config, 'p2p_tcp_', ns)
        for tcp in tcps:
            fns = ns+'_'+str(tcp)
            hard_clone_section(config, ns, fns)
            config.set(fns, 'local_port', str(tcp))
        config.remove_section(ns)
    else:
        config.remove_section('p2p_tcp_')

    if(udps is not None):
        nu = 'secret_udp_'+str(port)
        rename_section(config, 'secret_udp_', nu)
        for udp in udps:
            fns = nu+'_'+str(udp)
            hard_clone_section(config, nu, fns)
            config.set(fns, 'local_port', str(udp))
        config.remove_section(nu)
    else:
        config.remove_section('secret_udp_')

    log('trace', config.sections())
    with open('t_configs/generated_client.ini', 'w') as configfile:    # save
        config.write(configfile)
    log('success', 'server config created.')

if(args.cmd == 'expose'):
    # EXPOSE COMMANDS
    expose(args.tcp, args.udp)
elif(args.cmd == 'connect'):
    # connect COMMANDS
    pass
