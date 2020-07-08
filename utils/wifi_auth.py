#!/usr/bin/env python3

# hydrant utility, find the time it takes for a wireless access point to authenticate and connect to the internet
# script will run through once, and store gathered data in the database
# command utility to scrape: ?
# gather information: auth_time, ?

import sqlite3
import os
import subprocess
import datetime

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
    #c.execute('''CREATE TABLE {} (SYSTEM_NAME TEXT, SYSTEM_DESCRIPTION TEXT, PORT_ID TEXT, MANAGEMENT_IP TEXT, VLAN_ID INTEGER, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility
print("collecting data for table {}".format(table_name))

# find name of wireless interface:
output = subprocess.run("iw dev | grep -i Interface", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
output = output.split(" ")
wireless_interface = output[1][:-1]
print(wireless_interface)

# load wifi credentials
essid = "Outside Open"
passwd = "cylonbase4starswar"

# generate wpa passphrase:
wpa_pass = subprocess.run('wpa_passphrase "{}" "{}" | tee utils/temp/wpa_supplicant.conf'.format(essid, passwd), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
print(wpa_pass)

# connect to wireless access point
output = subprocess.run("sudo wpa_supplicant -c utils/temp/wpa_supplicant.conf -i {}".format(wireless_interface), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')











# parse the output into desired variables
    
    # store to table:   # quotes were added to some strings to comply with SQL syntax
    #c.execute('''INSERT INTO {} VALUES({}, {}, {}, {}, {}, {})'''.format(table_name, '"'+str(sysname)+'"', '"'+str(sysdescr)+'"', '"'+str(portid)+'"', '"'+str(mgmtip)+'"', vlanid, '"'+str(datetime.datetime.now())+'"'))

#commit the changes to db			
conn.commit()
#close the connection
conn.close()

