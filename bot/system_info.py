import getpass
import platform
import socket
import uuid

from shell_tools import run_cmd

### System
def get_platform():
    mac_version = str(platform.mac_ver()[0]).strip()
    if mac_version:
        return 'OS X %s' % mac_version
    return platform.platform().strip()

def get_current_user():
    return getpass.getuser()

def get_main_user():
    main_user = run_cmd("ps aux | grep CoreServices/Finder.app | head -1 | awk '{print $1}'")[0]

    if not main_user or main_user == 'root':
        main_user = run_cmd("stat -f '%Su' /dev/console")[0]

    return main_user

def get_full_username(user):
    full_name = run_cmd("finger %s | awk -F: '{ print $3 }' | head -n1 | sed 's/^ //'" % user)[0]
    return full_name or user

def get_hardware():
    return run_cmd('system_profiler SPHardwareDataType', verbose=False)[1:]

def get_power():
    return run_cmd("system_profiler SPPowerDataType | grep -q Connected && echo 'Connected' || echo 'Disconnected'")[0]

def get_uptime():
    return run_cmd('uptime')[0]

### Networking
def get_hostname():
    return socket.gethostname()

def get_local_ips():
    local_ips = run_cmd(r"ifconfig -a | perl -nle'/(\d+\.\d+\.\d+\.\d+)/ && print $1'")
    local_ips.remove('127.0.0.1')
    return local_ips

def get_public_ip():
    return run_cmd('dig +short myip.opendns.com @resolver1.opendns.com')[0]

def get_mac_addr():
    return ':'.join([
        '{:02x}'.format((uuid.getnode() >> i) & 0xff)
        for i in range(0,8*6,8)
    ][::-1])

def get_irc_nickname(full_name):
    return '[%s]' % full_name.replace(" ", "")[:14]


def get_location():
    # geo_info = geo_locate()
    # location = geo_info[0]+", "+geo_info[1]+" ("+str(geo_info[4])+", "+str(geo_info[5])+")"
    return 'Atlanta'
