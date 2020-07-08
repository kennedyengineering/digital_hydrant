#!/usr/bin/env python3

# hydrant utility, netdiscover ARP scan for reachable hosts
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo netdiscover -N -P
# gather information: IP, MAC_ADDRESS, HOSTNAME

import sqlite3
import os
import subprocess
import datetime

table_name = "netdiscover"

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
    c.execute('''CREATE TABLE {} (IP TEXT, MAC_ADDRESS TEXT, HOSTNAME TEXT, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility   # netdiscover either runs indefinetely or just a really long time, a timeout is needed, set in seconds
print("collecting data for table {}".format(table_name))
output = subprocess.run("sudo timeout 10 sudo netdiscover -N -P", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
#print(output)

# parse the output into desired variables
output = output.split("\n")
simplified_output = []
for i in output:
    temp_arr = []
    i = i.split(" ")
    for ii in i:
        if ii != '':
            temp_arr.append(ii)
    simplified_output.append(temp_arr)
simplified_output.remove([])

for i in simplified_output:
    # IP Adress
    ip = i[0]
    #print(ip)

    # MAC Address
    mac_address = i[1]
    #print(mac_address)

    # Hostname
    name = ""
    max_index = len(i)
    for ii in range(4, max_index):
        name += i[ii] + " "
    if name != "":
        name = name[:-1]
    #print(name)


    # store to table:   # quotes were added to some strings to comply with SQL syntax
    c.execute('''INSERT INTO {} VALUES({}, {}, {}, {})'''.format(table_name, '"'+str(ip)+'"', '"'+str(mac_address)+'"', '"'+str(name)+'"', '"'+str(datetime.datetime.now())+'"'))

#commit the changes to db			
conn.commit()
#close the connection
conn.close()

