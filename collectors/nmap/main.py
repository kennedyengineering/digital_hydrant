#!/usr/bin/env python3

# NMAP collector utility, find hosts, and port scan hosts
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo nmap -sn <interface IP>
# gather information: hostname, IP, latency, MAC address, open ports

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector
import ipaddress
import netifaces

# create collector
collector_name = "nmap"
collector = Collector(collector_name)

# find network IP to scan
iface = collector.misc_config['interface']
ifaces = netifaces.interfaces()
if iface not in ifaces:
    print(iface, "not available, exiting...")
    collector.close()
    exit()
else:
    print(iface, "available")

addrs = netifaces.ifaddresses(iface)[netifaces.AF_INET]
if len(addrs) == 0:
    print("no address available on", iface, "exiting...")
    collector.close()
    exit()
else:
    print("address available on", iface)

addr = addrs[0]
ip_addr = addr['addr']
subnet = addr['netmask']

net = str(ipaddress.ip_network('{}/{}'.format(ip_addr, subnet), strict=False))

# scan for hosts
command = "sudo nmap -sn {}".format(net)
output = collector.execute(command)

# parse output into host list
output = output.split("\n")
hosts = []
index = 0
for entry in output:
    if "Nmap scan report" in entry:
        host = []
        host.append(entry)
        if "Host is up" in output[index+1]:
            host.append(output[index+1])
            if "MAC Address" in output[index+2]:
                host.append(output[index+2])
                hosts.append(host)

    index += 1

for h in hosts:
    print(h)



# organize data into a dictionary for publishing
#parsed_output = {}
#parsed_output["DHCP_LOG"] = output
#collector.publish(parsed_output)

collector.close()
