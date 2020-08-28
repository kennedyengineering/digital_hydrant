#!/usr/bin/env python3

# Digital Hydrant 2020
# hydra collector utility, create target list from netdiscover data and test against default credential word list
# script will run through once, and store gathered data in the database
# command utility to scrape: hydra
# gather information: target, output log


# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector
import socket
import fcntl
import struct

# create collector
collector_name = "hydra"
collector = Collector(collector_name)

# collect current IP address, and subnet
iface = collector.misc_config['interface']
ip_addr =  socket.inet_ntoa(fcntl.ioctl(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), 0x8915, struct.pack('256s', str(iface[:15]).encode('utf-8')))[20:24])

def strip_ip(ip):
    ip_range_list = str(ip).split(".")
    del ip_range_list[3]
    return ip_range_list[0]+"."+ip_range_list[1]+"."+ip_range_list[2]+".0"

correct_ip = strip_ip(ip_addr)

target_ips = []

if collector.misc_config["enable_netdiscover"] == True:
    # find all IP's that are on the wrong subnet and add to target list
    collector.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='netdiscover';")
    result = collector.cursor.fetchall()
    if len(result) == 0:
        collector.logger.error("No netdiscover data available")
    else:
        collector.logger.debug("Found netdiscover data")

        collector.cursor.execute("SELECT IP FROM netdiscover WHERE IP NOT LIKE '{}%'".format(correct_ip[:-2]))
        netdiscover_target_ips = collector.cursor.fetchall()
        target_ips = target_ips + netdiscover_target_ips
        if len(netdiscover_target_ips) == 0:
            collector.logger.error("No IP's found to be on the wrong subnet")
else:
    collector.logger.debug("netdiscover data disabled via config, continuing")

if collector.misc_config["enable_nmap"] == True:
    # find all IP's with an open SSH port
    collector.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nmap';")
    result = collector.cursor.fetchall()
    if len(result) == 0:
        collector.logger.error("No nmap data available")
    else:
        collector.logger.debug("Found nmap data")

        collector.cursor.execute("SELECT IP FROM nmap WHERE OPEN_PORTS LIKE '{}%'".format("22/tcp"))
        nmap_target_ips = collector.cursor.fetchall()
        target_ips = target_ips + nmap_target_ips
        if len(nmap_target_ips) == 0:
            collector.logger.error("No IP's found with open SSH ports")
else:
    collector.logger.debug("nmap data disabled via config, continuing")


# remove duplicate IP's
target_ips = list(dict.fromkeys(target_ips))

# remove already scanned devices? Filter by TARGET column

command_ssh_template = "sudo hydra -I -L {} -P {} <hostname> ssh 2>&1 | tr '\n' ' '".format(collector.misc_config['userlist_path'], collector.misc_config['wordlist_path'])
command_snmp_template = "sudo hydra -I -P {} <hostname> snmp 2>&1 | tr '\n' ' '".format(collector.misc_config['wordlist_path'])

parsed_output = {}

for target in target_ips:
    target = target[0]

    collector.logger.debug("Operating on target {}, starting attack".format(target))

    # connect to subnet, create a new IP
    # use X.X.X.227 because it is rarely used
    if strip_ip(target) != correct_ip: 
        ip = strip_ip(target)[:-2] + ".227"
        collector.logger.debug("Joining {} network, with IP {}".format(strip_ip(target), ip))
        null = collector.execute("sudo ifconfig {}:1 {}".format(iface, ip))

    # scrape the command line utility
    ssh_output = collector.execute(command_ssh_template.replace("<hostname>", target))
    snmp_output = collector.execute(command_snmp_template.replace("<hostname>", target))
    
    #disconnect from subnet
    if strip_ip(target) != correct_ip:
        collector.logger.debug("Disconnecting from {} network".format(strip_ip(target)))
        null = collector.execute("sudo ifconfig {}:1 down".format(iface))

    # organize data into a dictionary for publishing
    parsed_output["TARGET"] = target
    parsed_output["SSH_OUTPUT_LOG"] = ssh_output
    parsed_output["SNMP_OUTPUT_LOG"] = snmp_output
    collector.publish(parsed_output)

collector.close()

