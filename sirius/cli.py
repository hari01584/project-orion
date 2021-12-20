import os
import re
import sys
import platform
import argparse
import subprocess
import configparser
import requests
import socket
import random
import time

class JustAException(Exception):
    pass


IS_DEBUG = False
def log(level, message):
    if(IS_DEBUG or level.lower() in ['fatal', 'out', 'check', 'success']):
        print('[%s] %s'%(level, message))

config = configparser.RawConfigParser()
config.read('server.ini')

try:
    SERVER_HOST = config['Server']['host']
    SERVER_PORT = config['Server']['port']
    SERVER_TOKEN = config['Server']['token']
except Exception:
    log("fatal", "server.ini corrupt or not found.")
    exit(-1)

config = configparser.RawConfigParser()
config.read('config.ini')
try:
    FRPC_FOLDER = config['Common']['dir']
    FRPC_EXECUTABLE = config['Common']['name']
    FRPS_EXECUTABLE = config['Common']['s_name']
except Exception:
    log("fatal", "config.ini corrupt or not found. please run ./get.py to repair")
    exit(-1)

def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def resolveHostname(host):
    param = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', '-6', param, '1', host]
    proc = subprocess.check_output(command)
    
    log('trace', 'packet %s'%(str(proc),))

    if(platform.system().lower()=='windows'):
        extrac = re.search('Reply from (.*?)(: time|%)', str(proc), re.IGNORECASE)
    else:
        extrac = re.search('(fe80:.*?%[a-z0-9\s]+)', str(proc), re.IGNORECASE)

    ipv = ''
    if extrac:
        ipv = extrac.group(1)
    else:
        log('trace', 'Exception occured, matching groups '+extrac.group(0))
        raise JustAException()

    log('trace', 'ip resolved address is %s'%(ipv,))
    log('trace', 'packet data: %s'%(proc,))

    return ipv

def c_verify_server_ping():
    global SERVER_HOST
    log("trace", "verifying valid server connection")
    try:
        SERVER_HOST = resolveHostname(SERVER_HOST) # TODO: MAYBE NOT GOOD
    except (subprocess.CalledProcessError, JustAException) as e:
        log('fatal', "Host server offline or unavaliable. Try switching wifi channel using windows app NetSetMan or linux command nmcli")
        exit(-1)

    log('check', "host server online.")

parser = argparse.ArgumentParser(prog='cli.py')
parser.add_argument('--debug', action='store_true')
parser.add_argument('-s', '--host', default='none', type=str)
parser.add_argument('-sp', '--secret-port', default=14541, type=int)

parser.add_argument('--no-host', action='store_true')

sp = parser.add_subparsers(dest='cmd')

expose_parser = sp.add_parser('expose')
expose_parser.add_argument('-t','--tcp', nargs='+', help='<Required> Set flag', type=int, required=False)
expose_parser.add_argument('-u','--udp', nargs='+', help='<Required> Set flag', type=int, required=False)

connect_parser = sp.add_parser('connect')
connect_parser.add_argument('port', type=int)

sp.add_parser('status')

args = parser.parse_args(sys.argv[1:])

IS_DEBUG = args.debug
SERVER_NO_HOST = args.no_host

if(args.host != 'none'):
    log('trace', 'server host provided in args, skipping checks')
    SERVER_HOST = args.host
elif(SERVER_NO_HOST):
    SERVER_NO_HOST = True
    SERVER_HOST = '::'
    SERVER_PORT = 14541
    if(args.cmd == 'connect'):
        log('out', 'no-host flag detected, please use -s or --host arg to pass host server address(pref. IPv6), You can find this address using the commands such as ipconfig(windows) or ip a (linux) on target machine')
        exit(-1)
else:
    c_verify_server_ping()

if(SERVER_NO_HOST):
    log('trace', 'enabling self-hosting feature, this might be unstable')

if(args.secret_port != 14541 and not SERVER_NO_HOST):
    log('trace', 'server port provided in args')
    SERVER_PORT = args.secret_port

def hard_clone_section(cp, section_from, section_to):
    items = cp.items(section_from)
    cp.add_section(section_to)
    for item in items:
        cp.set(section_to, item[0], item[1])

def rename_section(cp, section_from, section_to):
    hard_clone_section(cp, section_from, section_to)
    cp.remove_section(section_from)

def rename_key(cp, fns, key_from, key_to):
    d = cp.get(fns, key_from)
    cp.remove_option(fns, key_from)
    cp.set(fns, key_to, d)

def callfrpc(args):
    callable = [FRPC_FOLDER+'/'+FRPC_EXECUTABLE] + args
    log('trace', 'Calling frpc with args -> '+' '.join(callable))
    subprocess.call(callable)

def expose(tcps, udps):
    p_frps = None
    if(SERVER_NO_HOST):
        log('out', 'no_host enabled, starting frps server')
        p_frps = subprocess.Popen([FRPC_FOLDER+'/'+FRPS_EXECUTABLE, '-c', 't_configs/template_server_selfhost.ini'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p_frps.stdout:
            print(line)
            if('frps started successfully' in str(line)):
                log('success', 'started local frps successfully')
                break

    # Write configs
    config = configparser.RawConfigParser()
    config.read('t_configs/template_client.ini')

    config.set('common', 'server_addr', SERVER_HOST)
    config.set('common', 'server_port', SERVER_PORT)
    config.set('common', 'token', SERVER_TOKEN)

    port = random.randint(8000,65535)
    port = 14259 # TODO DEBUG
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

    log('out', 'generating client_connect config.')
    config.remove_section(nl)

    if(tcps is not None):
        ns = 'p2p_tcp_'+str(port)
        for tcp in tcps:
            fns = ns+'_'+str(tcp)
            config.set(fns, 'server_name', fns)
            config.set(fns, 'role', 'visitor')
            rename_key(config, fns, 'local_ip', 'bind_addr')
            rename_key(config, fns, 'local_port', 'bind_port')

            config.set(fns, 'bind_port', str(tcp))

    if(udps is not None):
        ns = 'secret_udp_'+str(port)
        for udp in udps:
            fns = ns+'_'+str(udp)
            config.set(fns, 'server_name', fns)
            config.set(fns, 'role', 'visitor')
            rename_key(config, fns, 'local_ip', 'bind_addr')
            rename_key(config, fns, 'local_port', 'bind_port')

            config.set(fns, 'bind_port', str(tcp))

    with open('t_configs/generated_client_connect.ini', 'w') as configfile:
        config.write(configfile)

    log('success', 'starting project_orion.')
    if(SERVER_NO_HOST):
        log('success', 'NOTE: NO HOST MODE IS ACTIVE, YOU HAVE TO USE --no-host FLAG WHILE CONNECTING USING SECRET PORT')
        log('success', 'syntax(to connect): python cli.py --no-host connect '+str(port))
    else:
        log('success', 'syntax(to connect): python cli.py connect '+str(port))
    callfrpc(['-c', 't_configs/generated_client.ini'])

    if(p_frps):
        p_frps.kill()

def scrapeConfigs(sport):
    url = 'http://127.0.0.1:'+str(sport)+'/generated_client_connect.ini'
    #while(True): pass
    r = requests.get(url, timeout=4)

    if(str(sport) not in str(r.content)):
        log('fatal', 'error, downloaded_client_config corrupt/invalid.')
        exit(-1)

    with open('t_configs/downloaded_client_connect.ini', 'wb') as fd:
        for chunk in r.iter_content(1024):
            fd.write(chunk)

    config = configparser.RawConfigParser()
    config.read('t_configs/downloaded_client_connect.ini')
    config.set('common', 'server_addr', SERVER_HOST)
    config.set('common', 'server_port', SERVER_PORT)
    with open('t_configs/downloaded_client_connect.ini', 'w') as configfile:
        config.write(configfile)

    return True

def connect(sport):
    log('out', 'initiating client handshake on port '+str(sport))
    config = configparser.RawConfigParser()
    config.read('t_configs/template_client_connector_handshake.ini')

    config.set('common', 'server_addr', SERVER_HOST)
    config.set('common', 'server_port', SERVER_PORT)
    config.set('common', 'token', SERVER_TOKEN)

    log('trace', 'starting with secret connector port %s'%(sport,))
    nl = 'link_'+str(sport)
    rename_section(config, 'link_', nl)
    log('trace', config.sections())
    config.set(nl, 'server_name', nl)
    config.set(nl, 'bind_port', sport)

    with open('t_configs/generated_client_connector_handshake.ini', 'w') as configfile:    # save
        config.write(configfile)
    log('trace', 'client_handshake config created.')

    log('out', 'verifying handshake and checking configuration.')

    cmd = [FRPC_FOLDER+'/'+FRPC_EXECUTABLE, '-c', 't_configs/generated_client_connector_handshake.ini']
    log('trace', 'executing => ' + ' '.join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    isBuilt = False
    for line in p.stdout:
        log('trace', line)
        if('visitor added: [link_' in str(line)):
            log('trace', 'handshake pipe established, fetching configs')
            try:
                isBuilt = scrapeConfigs(sport)
            except requests.exceptions.RequestException as e:
                log('fatal', 'error while downloading config, please recheck the connecting port.')
            p.kill()
    p.kill()
    if(not isBuilt):
        log('fatal', 'problem in requesting config from host.')
        exit(-1)

    log('success', 'downloaded client_connect config, starting tunneling of all ports')
    callfrpc(['-c', 't_configs/downloaded_client_connect.ini'])


if(args.cmd == 'expose'):
    # EXPOSE COMMANDS
    expose(args.tcp, args.udp)
elif(args.cmd == 'connect'):
    # connect COMMANDS
    connect(args.port)
    pass
