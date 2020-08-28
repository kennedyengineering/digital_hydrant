#!/usr/bin/env python3

# Digital Hydrant 2020
# hydrant utility, lldp - Link Layer Discovery Protocol, search for LLDP neighbors, get information on switches
# script will run through once, and store gathered data in the database
# command utility to scrape: lldpctl (-f json?)
# gather information: SysName, SysDescr, PortID, MgmtIP, vlan-id

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector
import json

# create collector
collector_name = "lldp"
collector = Collector(collector_name)

# scrape the command line utility
command = "lldpctl -f json"
output = collector.execute(command)

# parse the output into desired variables
output = json.loads(output)
try:
    for i in output["lldp"]["interface"]:   # iterate per interface
        parsed_output = {}

        # SysName
        sysname = list(output["lldp"]["interface"][i]["chassis"].keys())[0]
        parsed_output["SYSTEM_NAME"] = sysname

        # SysDescr
        sysdescr = output["lldp"]["interface"][i]["chassis"][sysname]["descr"].replace("\n", " ")
        parsed_output["SYSTEM_DESCRIPTION"] = sysdescr
       
        # PortID
        portid = output["lldp"]["interface"][i]["port"]["id"]["type"]
        portid += " " + output["lldp"]["interface"][i]["port"]["id"]["value"]
        parsed_output["PORT_ID"] = portid

        # MgmtIP
        mgmtip = output["lldp"]["interface"][i]["chassis"][sysname]["mgmt-ip"]
        parsed_output["MANAGEMENT_IP"] = mgmtip

        # vlan-id
        vlanid = int(output["lldp"]["interface"][i]["vlan"]["vlan-id"])
        parsed_output["VLAN_ID"] = vlanid

        # store to table
        collector.publish(parsed_output)

except KeyError as err:
    collector.logger.error("No interface found, with error {}".format(err))

collector.close()
