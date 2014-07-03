import scapy.all as scapy

pktcnt = 0
dest_mac_address = scapy.discover_mac_for_ip(dest_ip) # 
output_mac = scapy.get_if_hwaddr(output_interface)

def process_packet(pkt):

    pktcnt += 1
    p = pkt.copy()
    # if this packet has an IP layer, change the dst field
    # to our final destination
    if IP in p:
        p[IP].dst = dest_ip

    # if this packet has an ethernet layer, change the dst field
    # to our final destination. We have to worry about this since
    # we're using sendp (rather than send) to send the packet.  We
    # also don't fiddle with it if it's a broadcast address.
    if Ether in p \
       and p[Ether].dst != 'ff:ff:ff:ff:ff:ff':
        p[Ether].dst = dest_mac_address
        p[Ether].src = output_mac

    # use sendp to avoid ARP'ing and stuff
    sendp(p, iface=output_interface)
