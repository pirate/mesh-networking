import getpass
import platform
import socket
import uuid

from shell_tools import run_cmd

### System
def get_platform():
    """get Mac OS X version or kernel version if mac version is not found"""
    mac_version = str(platform.mac_ver()[0]).strip()    # e.g. 10.11.2
    if mac_version:
        return 'OS X %s' % mac_version
    return platform.platform().strip()                  # e.g. Darwin-15.4.0-x86_64-i386-64bit

def get_current_user():
    """guess the username this program is running under"""
    return getpass.getuser()

def get_main_user():
    """guess the primary user of the computer who is currently logged in"""
    # Guess main user by seeing who is currently running Finder.app
    main_user = run_cmd("ps aux | grep CoreServices/Finder.app | head -1 | awk '{print $1}'")[0]

    if not main_user or main_user == 'root':
        # fallback to guess main user by seeing who owns the console file
        main_user = run_cmd("stat -f '%Su' /dev/console")[0]

    return main_user

def get_full_username(user):
    """sarah -> Sarah J. Connor"""
    full_name = run_cmd("finger %s | awk -F: '{ print $3 }' | head -n1 | sed 's/^ //'" % user)[0]
    return full_name or user

def get_hardware():
    """detailed hardware overview from system profiler"""
    return run_cmd('system_profiler SPHardwareDataType', verbose=False)[1:]

def get_power():
    """detect whether computer is plugged in"""
    return run_cmd("system_profiler SPPowerDataType | grep -q Connected && echo 'Connected' || echo 'Disconnected'")[0]

def get_uptime():
    return run_cmd('uptime')[0]

### Networking
def get_hostname():
    return socket.gethostname()

def get_local_ips():
    """parse ifconfig for all the computer's local IP addresses"""
    local_ips = run_cmd(r"ifconfig -a | perl -nle'/(\d+\.\d+\.\d+\.\d+)/ && print $1'")
    local_ips.remove('127.0.0.1')
    return local_ips

def get_public_ip():
    """get the computer's current public IP by querying the opendns public ip resolver"""
    return run_cmd('dig +short myip.opendns.com @resolver1.opendns.com')[0]

def get_mac_addr():
    """get the computer's current internet-facing MAC address"""
    return ':'.join([
        '{:02x}'.format((uuid.getnode() >> i) & 0xff)
        for i in range(0,8*6,8)
    ][::-1])

def get_irc_nickname(full_name):
    """Sarah J. Connor -> [SarahJ.Connor]"""
    return '[%s]' % full_name.replace(" ", "")[:14]

def get_location():
    """guess the computer's current geolocation based on IP address"""
    # geo_info = geo_locate()
    # location = geo_info[0]+", "+geo_info[1]+" ("+str(geo_info[4])+", "+str(geo_info[5])+")"
    return 'Atlanta'


def add_gatekeeper_exception(app_path):
    """WARNING: big scary password prompt is shown to the current active user"""
    return run_cmd('spctl --add "%s"' % app_path)

def lock_screen():
    return run_cmd('/System/Library/CoreServices/Menu\ Extras/User.menu/Contents/Resources/CGSession -suspend')

def screensaver():
    return run_cmd('open /System/Library/Frameworks/ScreenSaver.framework/Versions/A/Resources/ScreenSaverEngine.app')
