#!/bin/bash

if which brew; then
    brew install --with-python libdnet
    brew install python3
else
    apt install libdnet python-dumbnet python3
end

# OR to install libdnet and bindings manually:
#
# git clone https://github.com/dugsong/libdnet.git
# cd libdnet
# sudo make && sudo make install
# cd libdnet-1.12/python/
# python setup.py install

echo "[√] Now run 'python3 lan-chat.py' on multiple computers to chat within a LAN."
