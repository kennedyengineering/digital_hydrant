#!/usr/bin/env python3

# Digital Hydrant 2020
# hydrant utility, find the time it takes for a wireless access point to authenticate and connect to the internet
# script will run through once, and store gathered data in the database
# command utility to scrape: None -- using timers
# gather information: auth_time, essid, inet6_address, AP address, link_quality, signal_level, frequency, bit_rate, Tx-Power

# import collector module from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collector import Collector
import subprocess
import time

# create collector
collector_name = "wifi_auth"
collector = Collector(collector_name)

# load ESSID and password from passed arguments
if len(sys.argv) != 3:
    collector.logger.error("2 parameters expected, ESSID and password, exiting")
    collector.close()
    exit()
essid = sys.argv[1]
passwd = sys.argv[2]

# scrape the command line utility(s)

# find name of wireless interface:
output = subprocess.run("iw dev | grep Interface", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
output = output.split(" ")
wireless_interface = output[1][:-1]
collector.logger.debug("Found wireless interface: {}".format(wireless_interface))

# generate wpa passphrase:
wpa_pass = subprocess.run('wpa_passphrase "{}" "{}" | tee collectors/wifi_auth/wpa_supplicant.conf'.format(essid, passwd), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

# connect to wireless access point
collector.logger.debug("Attempting to connect to wireless access point {}".format(essid))
tic = time.perf_counter()
wpa_supplicant = subprocess.Popen("sudo wpa_supplicant -c collectors/wifi_auth/wpa_supplicant.conf -i {}".format(wireless_interface), shell=True, stdout=subprocess.PIPE)
auth_timeout = collector.exec_duration
auth_time = -1
for line in iter(wpa_supplicant.stdout.readline, ''):
    line = line.decode('utf-8')
    toc = time.perf_counter()
    auth_time = toc-tic
    if line.find("CTRL-EVENT-CONNECTED") != -1:
        collector.logger.debug("Wireless is connected")
        break
    elif auth_time > auth_timeout:
        collector.logger.error("Authentication timeout reached, exiting")
        auth_time = -1
        break

# parse connection details
parsed_output = {}

if auth_time != -1:
    parsed_output["AUTH_TIME"] = auth_time

    # check for inet6 IP address
    inet6_addr = ""
    output = subprocess.run("ifconfig", shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    # split by empty line
    output = output.split("\n\n")
    line = None
    for interface in output:
        if interface.find(wireless_interface) != -1:
            line = interface
            break
    if line is not None:
        if line.find("inet6") != -1:
            # find IP address
            line = line.split("\n")
            for group in line:
                if group.find("inet6") != -1:
                    line = group
                    break
            line = line.split()
            inet6_addr = line[1]
            collector.logger.debug("Inet6 IP obtained")
        else:
            collector.logger.error("No inet6 IP address found")
    else:
        collector.logger.error("No inet6 IP address found")
    parsed_output["INET6_ADDRESS"] = inet6_addr

    # check AP address, check link quality, check signal level, check frequency, check bit rate, check tx power
    AP_address = ""
    link_quality = ""
    signal_level = ""
    frequency = ""
    bit_rate = ""
    tx_power = ""
    loaded = False  # sometimes there will be an index out of range error because iwconfig hasn't loaded all variables by time of polling   # instead of waiting, poll again so it runs as fast as possible
    poll_counter = 0
    poll_max = 5    # limit number of times it can poll iwconfig
    while not loaded:
        try:
            output = subprocess.run("iwconfig 2>&1 | grep -v 'no wireless extensions'", shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
            # split by empty line
            output = output.split("\n\n")
            # find entry for wireless interface in use
            for interface in output:
                if interface.find(wireless_interface) != -1:
                    line = interface
                    break

            # process data
            line = line.split("  ")

            # check AP address
            entry = ""
            for group in line:
                if group.find("Access Point") != -1:
                    entry = group
                    break
            entry = entry.split()
            AP_address = entry[2]

            # check link quality
            entry = ""
            for group in line:
                if group.find("Link Quality") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            link_quality = entry[1]

            # check signal level
            entry = ""
            for group in line:
                if group.find("Signal level") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            signal_level = entry[1]

            # check frequency
            entry = ""
            for group in line:
                if group.find("Frequency") != -1:
                    entry = group
                    break
            entry = entry.split(":")
            frequency = entry[1]

            # check bit rate
            entry = ""
            for group in line:
                if group.find("Bit Rate") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            bit_rate = entry[1]

            # check tx power
            entry = ""
            for group in line:
                if group.find("Tx-Power") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            tx_power = entry[1]

            loaded = True

        except Exception as err:
            poll_counter += 1
            if poll_counter > poll_max:
                collector.logger.error("Unable to scrap iwconfig")
                break
            collector.logger.error("Error scraping iwconfig, attempt {}/{}, retrying".format(poll_counter, poll_max))
            loaded = False
            time.sleep(0.2)

    parsed_output["AP_ADDRESS"] = AP_address
    parsed_output["LINK_QUALITY"] = link_quality
    parsed_output["SIGNAL_LEVEL"] = signal_level
    parsed_output["FREQUENCY"] = frequency
    parsed_output["BIT_RATE"] = bit_rate
    parsed_output["TX_POWER"] = tx_power

    parsed_output["ESSID"] = essid

    collector.publish(parsed_output)

# kill the process if it is still running
wpa_supplicant.kill()

# start DHClient to check IPv4 address
# sudo dhclient wlan0

# bring wireless interface down and up again "reset it"
os.system("sudo ifconfig {} down".format(wireless_interface))
os.system("sudo ifconfig {} up".format(wireless_interface))

# delete temp files
# rm utils/temp/wpa_supplicant.conf
os.remove("collectors/wifi_auth/wpa_supplicant.conf")

collector.close()
