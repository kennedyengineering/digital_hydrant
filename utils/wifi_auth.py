#!/usr/bin/env python3

# hydrant utility, find the time it takes for a wireless access point to authenticate and connect to the internet
# script will run through once, and store gathered data in the database
# command utility to scrape: None -- using timers
# gather information: auth_time, ?

import sqlite3
import os
import subprocess
import datetime
import time
import sys

# check parameters, use for essid and passwd variable definitions   # 3 because the first is the file name -- wifi_auth.py
if len(sys.argv) != 3:
    print("ESSID and PASSWD were not provided, exiting")
    exit()
essid = sys.argv[1]
passwd = sys.argv[2]
#print(essid, passwd)

table_name = "wifi_auth"

# load variables from config file
db_name = os.environ["db_name"]
drive_path = os.environ["drive_path"]
# connect to the SQLite3 database
conn = sqlite3.connect(str(drive_path) + "/" + str(db_name))
c = conn.cursor()
# verify that the table exists, get a count
c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}' '''.format(table_name))
# if the count is 1, then table exists
# else, create the table    # could use CREATE TABLE IF NOT EXISTS to eliminate the need to check if the table exists
if c.fetchone()[0]==1 :
    print("table exists for {}, continuing".format(table_name))
else:
    print("no table exists for {}, creating".format(table_name))
    c.execute('''CREATE TABLE {} (AUTH_TIME TEXT, ESSID TEXT, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility
print("collecting data for table {}".format(table_name))

# find name of wireless interface:
output = subprocess.run("iw dev | grep Interface", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
output = output.split(" ")
wireless_interface = output[1][:-1]
#print(wireless_interface)

# generate wpa passphrase:
wpa_pass = subprocess.run('wpa_passphrase "{}" "{}" | tee utils/temp/wpa_supplicant.conf'.format(essid, passwd), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
#print(wpa_pass)

# connect to wireless access point
tic = time.perf_counter()
wpa_supplicant = subprocess.Popen("sudo wpa_supplicant -c utils/temp/wpa_supplicant.conf -i {}".format(wireless_interface), shell=True, stdout=subprocess.PIPE)
auth_timeout = 30
for line in iter(wpa_supplicant.stdout.readline, ''):
    line = line.decode('utf-8')
    print(line)
    toc = time.perf_counter()
    auth_time = toc-tic
    if line.find("CTRL-EVENT-CONNECTED") != -1:
        print("Wireless is Connected")
        print("Authentication time: {} seconds".format(auth_time))
        break
    elif auth_time > auth_timeout:
        print("Authentication timeout reached, exiting...")
        auth_time = -1
        break
    elif line.find("CTRL-EVENT-DISCONNECTED") != -1:
        print("Authentication failed, exiting...")
        auth_time = -1
        break

wpa_supplicant.kill()

# start DHClient
# sudo dhclient wlan0

# bring wireless interface down and up again "reset it"
os.system("sudo ifconfig {} down".format(wireless_interface))
os.system("sudo ifconfig {} up".format(wireless_interface))

# delete temp files
# rm utils/temp/wpa_supplicant.conf
os.remove("utils/temp/wpa_supplicant.conf")

# parse the output into desired variables
# store to table:   # quotes were added to some strings to comply with SQL syntax
c.execute('''INSERT INTO {} VALUES("{}", "{}", "{}")'''.format(table_name, str(auth_time), str(essid), str(datetime.datetime.now())))

#commit the changes to db			
conn.commit()
#close the connection
conn.close()

