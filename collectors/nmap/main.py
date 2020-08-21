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
import re

# create collector
collector_name = "nmap"
collector = Collector(collector_name)

# find network IP to scan
iface = collector.misc_config['interface']
ifaces = netifaces.interfaces()
if iface not in ifaces:
    collector.logger.error("Interface {} not available, exiting...".format(iface))
    collector.close()
    exit()
else:
    collector.logger.debug("Interface {} available".format(iface))

addrs = netifaces.ifaddresses(iface)[netifaces.AF_INET]
if len(addrs) == 0:
    collector.logger.error("No address available on interface {}, exiting...".format(iface))
    collector.close()
    exit()
else:
    collector.logger.debug("Address available on interface {}".format(iface))

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

for host in hosts:
    parsed_output = {}

    # find IP address
    ip = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', host[0]).group()

    parsed_output["IP"] = ip

    # perform a port scan
    command = "sudo nmap -sS {}".format(ip)
    output = collector.execute(command)
    
    parsed_output["SCAN_LOG"] = output.replace("\n", " ")

    # parse output into port list
    output = output.split("\n")
    port_list = []
    index = 0
    for entry in output:
        if "PORT" in entry:
            index += 1
            while True:
                if "MAC Address" in output[index]:
                    break
                else:
                    port_list.append(output[index])
                    index += 1

        index += 1

    port_string = ""
    for port in port_list:
        port = port.split(" ")
        port = port[0]
        port_string = port_string + str(port) + " "
    port_string = port_string[:-1]
       
    parsed_output["OPEN_PORTS"] = port_string

    collector.publish(parsed_output)

collector.close()

