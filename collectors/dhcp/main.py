#!/usr/bin/env python3

# DHCP collector utility, record dynamic host configuration protocol data
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo dhcpcd -T {interface (optional)}
# gather information: all DHCP information--log

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector

# create collector
collector_name = "dhcp"
collector = Collector(collector_name)

# scrape the command line utility
command = "sudo dhcpcd -T"
output = collector.execute(command)

# organize data into a dictionary for publishing
parsed_output = {}
parsed_output["DHCP_LOG"] = output
parsed_output["TEST"] = 2
collector.publish(parsed_output)

collector.close()
