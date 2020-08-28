#!/usr/bin/env python3

# Digital Hydrant 2020
# network speed test collector utility, tests the upload/download speed of the network
# script will run through once, and store gathered data in the database
# command utility to scrape: speedtest-cli --simple
# gather information: ping, download, upload

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector

# create collector
collector_name = "speedtest"
collector = Collector(collector_name)

# scape the command line utility
command = "speedtest-cli --simple"
output = collector.execute(command)

# parse the output into desired variables
output = output.split("\n")
parsed_output = {}
for entry in output:
    if entry.find("Ping") != -1:
        ping = entry
        ping = ping.split(": ")
        ping = ping[1]
        parsed_output["PING"] = ping

    elif entry.find("Download") != -1:
        download = entry
        download = download.split(": ")
        download = download[1]
        parsed_output["DOWNLOAD"] = download

    elif entry.find("Upload") != -1:
        upload = entry
        upload = upload.split(": ")
        upload = upload[1]
        parsed_output["UPLOAD"] = upload

collector.publish(parsed_output)

collector.close()
