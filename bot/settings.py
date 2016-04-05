"""Bot config"""

import getpass
import os
import socket

from system_info import (
    get_hostname,
    get_platform,
    get_current_user,
    get_main_user,
    get_full_username,
    get_irc_nickname,
)


### System Info
HOSTNAME = get_hostname()
SYSTEM = get_platform()
LOCAL_USER = get_current_user()
MAIN_USER = get_main_user()
MAIN_USER_FULL = get_full_username(MAIN_USER)



### Bot IRC Setup
VERSION = '8.4'
ADMINS = ['thesquash']
NICK = get_irc_nickname(MAIN_USER_FULL)

IRC_CONNECTIONS = [
    {'server': 'irc.freenode.net', 'port': 6667, 'channel': '##medusa', 'nick': NICK},
]
