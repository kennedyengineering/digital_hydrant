#!/usr/bin/env python3

# Digital Hydrant 2020
# hydrant utility, netdiscover ARP scan for reachable hosts
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo netdiscover -N -P
# gather information: IP, MAC_ADDRESS, HOSTNAME

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector
import subprocess

# create collector
collector_name = "netdiscover"
collector = Collector(collector_name)

# scrape the command line utility
command = "sudo netdiscover -N -P"
if collector.exec_duration != -1:
    command = "sudo timeout {} ".format(collector.exec_duration) + command
collector.logger.debug("Broadcasting to 255.255.255.255 network")
broadcast_proc = subprocess.Popen("ping -b 255.255.255.255 2>&1", shell=True, stdout=subprocess.PIPE)
collector.logger.debug("Executing {}".format(command))
output = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
broadcast_proc.kill()

# parse the output into desired variables
output = output.split("\n")
simplified_output = []
for i in output:
    temp_arr = []
    i = i.split(" ")
    for ii in i:
        if ii != '':
            temp_arr.append(ii)
    simplified_output.append(temp_arr)
simplified_output.remove([])

for i in simplified_output:
    parsed_output = {}

    # IP Adress
    ip = i[0]
    parsed_output["IP"] = ip

    # MAC Address
    mac_address = i[1]
    parsed_output["MAC_ADDRESS"] = mac_address

    # Hostname
    name = ""
    max_index = len(i)
    for ii in range(4, max_index):
        name += i[ii] + " "
    if name != "":
        name = name[:-1]
    parsed_output["HOSTNAME"] = name

    collector.publish(parsed_output)

collector.close()
