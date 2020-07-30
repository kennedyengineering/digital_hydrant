#!/usr/bin/env python3

# hydrant utility, find the time it takes for a wireless access point to authenticate and connect to the internet
# script will run through once, and store gathered data in the database
# command utility to scrape: None -- using timers
# gather information: auth_time, essid, inet6_address, AP address, link_quality, signal_level, frequency, bit_rate, Tx-Power

################IMPORT STATEMENTS#################
import sqlite3
import os
import subprocess
import datetime
import time
import sys
from modules.log import log
from modules.upload import upload

# load variables from config file
db_name = os.environ["db_name"]
drive_path = os.environ["drive_path"]
# connect to the SQLite3 database
conn = sqlite3.connect(str(drive_path) + "/" + str(db_name))
c = conn.cursor()
# check parameters, use for essid and passwd variable definitions   # 3 because the first is the file name -- wifi_auth.py
if len(sys.argv) != 4:
    log("3 parameters expected, exiting...", error=True)
    exit()
timeout = sys.argv[1]
essid = sys.argv[2]
passwd = sys.argv[3]
#print(essid, passwd)
##################################################

# create table if it does not exist
table_name = "wifi_auth"
c.execute('''CREATE TABLE IF NOT EXISTS {} (AUTH_TIME TEXT, ESSID TEXT, INET6_ADDRESS TEXT, AP_ADDRESS TEXT, LINK_QUALITY TEXT, SIGNAL_LEVEL TEXT, FREQUENCY TEXT, BIT_RATE TEXT, TX_POWER TEXT, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility
log("collecting data for table {}".format(table_name))

# find name of wireless interface:
output = subprocess.run("iw dev | grep Interface", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
output = output.split(" ")
wireless_interface = output[1][:-1]
#print(wireless_interface)

# generate wpa passphrase:
wpa_pass = subprocess.run('wpa_passphrase "{}" "{}" | tee utils/temp/wpa_supplicant.conf'.format(essid, passwd), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
#print(wpa_pass)

# connect to wireless access point
log("Testing authentication time...")
tic = time.perf_counter()
wpa_supplicant = subprocess.Popen("sudo wpa_supplicant -c utils/temp/wpa_supplicant.conf -i {}".format(wireless_interface), shell=True, stdout=subprocess.PIPE)
auth_timeout = int(timeout)
auth_time = -1
for line in iter(wpa_supplicant.stdout.readline, ''):
    line = line.decode('utf-8')
    print(line)
    toc = time.perf_counter()
    auth_time = toc-tic
    if line.find("CTRL-EVENT-CONNECTED") != -1:
        log("Wireless is Connected")
        log("Authentication time: {} seconds".format(auth_time))
        break
    elif auth_time > auth_timeout:
        log("Authentication timeout reached, exiting...", error=True)
        auth_time = -1
        break
    elif line.find("CTRL-EVENT-DISCONNECTED") != -1:
        log("Authentication failed, exiting...", error=True)
        auth_time = -1
        break

# check for inet6 IP address
inet6_addr = ""
if auth_time != -1:
    output = subprocess.run("ifconfig", shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    # split by empty line
    output = output.split("\n\n")
    line = None
    for interface in output:
        if interface.find(wireless_interface) != -1:
            line = interface
            break
    if line.find("inet6") != -1:
        # find IP address
        line = line.split("\n")
        for group in line:
            if group.find("inet6") != -1:
                line = group
                break
        line = line.split()
        log("inet6 IP obtained: "+str(line[1]))
        inet6_addr = line[1]
    else:
        log("No IP found", error=True)

# check AP address, check link quality, check signal level, check frequency, check bit rate, check tx power
AP_address = ""
link_quality = ""
signal_level = ""
frequency = ""
bit_rate = ""
tx_power = ""
loaded = False  # sometimes there will be an index out of range error because iwconfig hasn't loaded all variables by time of polling   # instead of waiting, poll again so it runs as fast as possible
while loaded == False:
    try:
        if auth_time != -1:
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
            #print(line)
            
            # check AP address
            entry = ""
            for group in line:
                if group.find("Access Point") != -1:
                    entry = group
                    break
            entry = entry.split()
            AP_address = entry[2]
            #print(AP_address)

            # check link quality
            entry = ""
            for group in line:
                if group.find("Link Quality") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            link_quality = entry[1]
            #print(link_quality)

            # check signal level
            entry = ""
            for group in line:
                if group.find("Signal level") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            signal_level = entry[1]
            #print(signal_level)

            # check frequency
            entry = ""
            for group in line:
                if group.find("Frequency") != -1:
                    entry = group
                    break
            entry = entry.split(":")
            frequency = entry[1]
            #print(frequency)

            # check bit rate
            entry = ""
            for group in line:
                if group.find("Bit Rate") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            bit_rate = entry[1]
            #print(bit_rate)

            # check tx power
            entry = ""
            for group in line:
                if group.find("Tx-Power") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            tx_power = entry[1]
            #print(tx_power)

            loaded = True
    except IndexError:
        log("Error scraping iwconfig, retrying...", error=True)
        loaded = False

wpa_supplicant.kill()

# start DHClient to check IPv4 address
# sudo dhclient wlan0

# bring wireless interface down and up again "reset it"
os.system("sudo ifconfig {} down".format(wireless_interface))
os.system("sudo ifconfig {} up".format(wireless_interface))

# delete temp files
# rm utils/temp/wpa_supplicant.conf
os.remove("utils/temp/wpa_supplicant.conf")

# store to table:   # quotes were added to some strings to comply with SQL syntax
date = str(datetime.datetime.now())
c.execute('''INSERT INTO {} VALUES("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")'''.format(table_name, str(auth_time), str(essid), str(inet6_addr), str(AP_address), str(link_quality), str(signal_level), str(frequency), str(bit_rate), str(tx_power), date))
conn.commit()
upload(table_name, date)

#commit the changes to db			
conn.commit()
#close the connection
conn.close()
