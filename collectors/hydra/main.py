#!/usr/bin/env python3

# hydra collector utility, create target list from netdiscover data and test against default credential word list
# script will run through once, and store gathered data in the database
# command utility to scrape: hydra....
# gather information: accessed [Y/N], found credentials


# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector

# create collector
collector_name = "hydra"
collector = Collector(collector_name)

# capital -L for user list, capital -P for password list, do both at the same time? --> exponential execution time...
# different protocols? start with ssh. wtf is snmp? prob for switches?
# hydra -L userlist.txt -P wordlist.txt <hostname> ssh
# hydra -P wordlist.txt <hostname> snmp

print(collector.misc_config['wordlist_path'])

# scrape the command line utility
command = ""
output = collector.execute(command)

# organize data into a dictionary for publishing
parsed_output = {}
#parsed_output["DHCP_LOG"] = output
#collector.publish(parsed_output)

collector.close()

