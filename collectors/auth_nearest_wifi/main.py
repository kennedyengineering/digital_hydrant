#!/usr/bin/env python3

# nearest wireless network authentication timer, scans for nearest wireless networks and tests authentication time
# script will run through once, and store gathered data in the database
# command utility to scrape: built from wifi_quality.py and wifi_auth.py
# gather information: same as wifi_auth.py

################IMPORT STATEMENTS#################
import sqlite3
import os
import subprocess
import datetime
import time
import sys
from modules.log import log
from modules.upload import upload
import yaml

# load variables from config file
db_name = os.environ["db_name"]
drive_path = os.environ["drive_path"]
# connect to the SQLite3 database
conn = sqlite3.connect(str(drive_path) + "/" + str(db_name))
c = conn.cursor()
if len(sys.argv) != 2: # should be 3 in final version
    log("2 parameters expected, exiting...", error=True)
    exit()
timeout = sys.argv[1]
#num_networks = sys.argv[2]
num_networks = 3
##################################################

# create table if it does not exist
table_name = "auth_nearest_wifi"
c.execute('''CREATE TABLE IF NOT EXISTS {} (AUTH_TIME TEXT, ESSID TEXT, INET6_ADDRESS TEXT, AP_ADDRESS TEXT, LINK_QUALITY TEXT, SIGNAL_LEVEL TEXT, FREQUENCY TEXT, BIT_RATE TEXT, TX_POWER TEXT, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility
log("collecting data for table {}".format(table_name))
if timeout == "-1":     output = subprocess.run("sudo iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID' | tr -d '\n'", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
else:                   output = subprocess.run("sudo timeout {} sudo iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID' | tr -d '\n'".format(timeout), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

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

network_dict = {}
for i in res:
    # get variables per cell

    # address:
    address = i[i.index("Address:") + 1]
    #print(address)

    # encryption:
    encryption = i[i.index("Encryption") + 1]
    #print(encryption)

    # quality:
    value = None
    for ii in i:
        if "Quality" in ii:
            value = ii
            break
    value = value.split("=")
    quality = value[1]
    #print(quality)

    # last beacon:
    last_beacon = i[i.index("beacon:") + 1]
    #print(last_beacon)

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
    #print(essid)

    network_dict[str(essid)] = quality

# sort networks by signal strength, then truncate by desired amount of networks to test against
sort_orders = sorted(network_dict.items(), key=lambda x: x[1], reverse=True)
del sort_orders[num_networks:]

# find name of wireless interface:
output = subprocess.run("iw dev | grep Interface", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
output = output.split(" ")
wireless_interface = output[1][:-1]

# parse YAML config file
config_path = "config/wireless_network_credentials.yml"
log("parsing "+config_path)
with open(config_path) as f:
    data = yaml.load(f, Loader=yaml.FullLoader)
    try:
        data = data["networks"]
    except KeyError:
        log("failed to parse "+config_path, error=True)

# match discovered networks to cached credentials, only operate on networks with cached credentials
network_creds = []
for entry in sort_orders:
    name = entry[0][1:-1]   # [1:-1] strips the double quotes from the string AKA removes first and last characters
    for cred in data:
        if cred["essid"] == name:
            network_creds.append([name, cred["passwd"]])

if len(network_creds) != len(sort_orders):
    diff = len(network_creds)
    log("Not all discovered networks have cached credentials: operating on "+str(diff)+"/"+str(num_networks)+" networks", error=True)

for entry in network_creds:
    log("Operating on discovered network: "+entry[0])
    essid = entry[0]
    passwd = entry[1]

    # generate wpa passphrase:
    wpa_pass = subprocess.run('wpa_passphrase "{}" "{}" | tee utils/temp/wpa_supplicant.conf'.format(essid, passwd), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

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
    while loaded == False and auth_time != -1:
        try:
            output = subprocess.run("iwconfig 2>&1 | grep -v 'no wireless extensions'", shell=True,
                                    stdout=subprocess.PIPE).stdout.decode("utf-8")
            # split by empty line
            output = output.split("\n\n")
            # find entry for wireless interface in use
            for interface in output:
                if interface.find(wireless_interface) != -1:
                    line = interface
                    break

            # process data
            line = line.split("  ")
            # print(line)

            # check AP address
            entry = ""
            for group in line:
                if group.find("Access Point") != -1:
                    entry = group
                    break
            entry = entry.split()
            AP_address = entry[2]
            # print(AP_address)

            # check link quality
            entry = ""
            for group in line:
                if group.find("Link Quality") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            link_quality = entry[1]
            # print(link_quality)

            # check signal level
            entry = ""
            for group in line:
                if group.find("Signal level") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            signal_level = entry[1]
            # print(signal_level)

            # check frequency
            entry = ""
            for group in line:
                if group.find("Frequency") != -1:
                    entry = group
                    break
            entry = entry.split(":")
            frequency = entry[1]
            # print(frequency)

            # check bit rate
            entry = ""
            for group in line:
                if group.find("Bit Rate") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            bit_rate = entry[1]
            # print(bit_rate)

            # check tx power
            entry = ""
            for group in line:
                if group.find("Tx-Power") != -1:
                    entry = group
                    break
            entry = entry.split("=")
            tx_power = entry[1]
            # print(tx_power)

            loaded = True

        except IndexError:
            log("Error scraping iwconfig", error=True)
            break

    wpa_supplicant.kill()
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
    # mark the data entry for uploading
    upload(table_name, date)

    # allow interface to reset and other unhandlable services complete
    time.sleep(2)

#commit the changes to the database
conn.commit()
#close the connection
conn.close()
