#!/usr/bin/env python3

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

# find all IP's that are on the wrong subnet and add to target list
collector.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='netdiscover';")
result = collector.cursor.fetchall()
if len(result) == 0:
    collector.logger.error("No netdiscover data available, exiting...")
    collector.close()
    exit()
else:
    collector.logger.debug("Found netdiscover data")

collector.cursor.execute("SELECT IP FROM netdiscover WHERE IP NOT LIKE '{}%'".format(correct_ip[:-2]))
target_ips = (collector.cursor.fetchall())
if len(target_ips) == 0:
    collector.logger.error("No IP's found to be on the wrong subnet, exiting...")
    collector.close()
    exit()

# remove duplicate IP's
target_ips = list(dict.fromkeys(target_ips))

command_ssh_template = "sudo hydra -I -L {} -P {} <hostname> ssh 2>&1".format(collector.misc_config['userlist_path'], collector.misc_config['wordlist_path'])
command_snmp_template = "sudo hydra -I -P {} <hostname> snmp 2>&1".format(collector.misc_config['wordlist_path'])

parsed_output = {}

for target in target_ips:
    target = target[0]

    collector.logger.debug("Operating on target {}, starting attack".format(target))

    output_log = ""
    
    # scrape the command line utility
    output = collector.execute(command_ssh_template.replace("<hostname>", target))
    output_log = output_log + output + "\n"
    output = collector.execute(command_snmp_template.replace("<hostname>", target))
    output_log = output_log + output + "\n"
    
    # organize data into a dictionary for publishing
    parsed_output["TARGET"] = target
    parsed_output["OUTPUT_LOG"] = output_log
    collector.publish(parsed_output)

    break

collector.close()

