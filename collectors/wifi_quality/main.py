#!/usr/bin/env python3

# Digital Hydrant 2020
# hydrant utility, search for nearby wireless accesspoints
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID'
# gather information: encryption, quality, last beacon, ESSID

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector

# create collector
collector_name = "wifi_quality"
collector = Collector(collector_name)

# scrape the command line utility
command = "sudo iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID' | tr -d '\n'"
output = collector.execute(command)

# parse the output into desired variables
# remove spaces and place words into an array
output = output.split(" ")
simplified_output = []
for i in output:
    if i != '':
        simplified_output.append(i)

# this data is reported in cells, split data into cells
# using list comprehension + zip() + slicing + enumerate() 
size = len(simplified_output) 
idx_list = [idx for idx, val in
            enumerate(simplified_output) if val == "Cell"] 
res = [simplified_output[i: j] for i, j in
        zip([0] + idx_list, idx_list + 
        ([size] if idx_list[-1] != size else []))]
res.remove([])

for i in res:
    parsed_output = {}
    # get variables per cell

    # address:
    address = i[i.index("Address:") + 1]
    parsed_output["ADDRESS"] = address

    # encryption: 
    encryption = i[i.index("Encryption") + 1]
    parsed_output["ENCRYPTION"] = encryption

    # quality:
    value = None
    for ii in i:
        if "Quality" in ii:
            value = ii
            break
    value = value.split("=")
    quality = value[1]
    parsed_output["QUALITY"] = quality

    # last beacon:
    last_beacon = i[i.index("beacon:") + 1]
    parsed_output["LAST_BEACON"] = last_beacon

    # ESSID:
    value = None
    for ii in i:
        if "ESSID" in ii:
            value = ii
            break
    index = i.index(value)
    # compensate for ESSID's with whitespace
    x = 0
    value = ""
    while i[index + x] != "Extra:":
        value += i[index + x] + " "
        x += 1
    if value != "":
        value = value[:-1]
    value = value.split(":")
    essid = value[1]
    essid = essid[:-1][1:]
    parsed_output["ESSID"] = essid

    # store to table
    collector.publish(parsed_output)

collector.close()
