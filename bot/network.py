# -*- coding: utf-8 -*-

import time, socket

def portscan(host='127.0.0.1', max_port=1000):
    yield 'Starting Singlethreaded Portscan of %s.' % host
    benchmark = time.time()
    try:
        remoteServerIP  = socket.gethostbyname(host)
    except Exception as e:
        yield e

    ports = []
    for port in range(1,max_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if s.connect_ex((remoteServerIP, port)) == 0:
            ports.append(port)
            yield port
        s.close()

    yield ports
    yield 'Finished Scan in %ss.' % str(round(time.time() - benchmark,2))


def power_on_wifi(iface='en0'):
    return run_cmd('networksetup -setairportpower %s on' % iface)

def current_wifi():
    return run_cmd("/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | awk '/ SSID/ {print substr($0, index($0, $2))}'")

def list_wifis():
    return run_cmd('/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport --scan')

def join_wifi(name, password='', iface='en0'):
    return run_cmd('networksetup -setairportnetwork %s %s %s' % (iface, name, password))

def get_wifi_password(name):
    """WARNING: prompts the user for their keychain password, but the prompt is very generic"""
    return run_cmd('security find-generic-password -D "AirPort network password" -a "%s" -gw' % name)

def disable_firewall():
    return run_cmd('sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off')
