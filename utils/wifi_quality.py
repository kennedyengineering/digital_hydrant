#!/usr/bin/env python3

# hydrant utility, search for nearby wireless accesspoints
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID'
# gather information: encryption, quality, last beacon, ESSID

import sqlite3
import os
import subprocess

table_name = "wifi_quality"

# load variables from config file
db_name = os.environ["db_name"]
drive_path = os.environ["drive_path"]

conn = sqlite3.connect(str(drive_path) + "/" + str(db_name))
c = conn.cursor()

# verify that the table exists, get a count
c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}' '''.format(table_name))

#if the count is 1, then table exists
if c.fetchone()[0]==1 :
    print("table exists for {}, continuing".format(table_name))
else:
    print("no table exists for {}, creating".format(table_name))
    #c.execute('''CREATE TABLE students (rollno real, name text, class real)''')

# scrape the command line utility
output = subprocess.run("sudo iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID' | tr -d '\n'", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
#print(output)

# parse the output into desired variables
# remove spaces and place words into an array
output = output.split(" ")
simplified_output = []
for i in output:
    if i != '':
        simplified_output.append(i)
#print(simplified_output)

# this data is reported in cells, split data into cells
# using list comprehension + zip() + slicing + enumerate() 
size = len(simplified_output) 
idx_list = [idx for idx, val in
            enumerate(simplified_output) if val == "Cell"] 
res = [simplified_output[i: j] for i, j in
        zip([0] + idx_list, idx_list + 
        ([size] if idx_list[-1] != size else []))]
res.remove([])
#print(res)

#commit the changes to db			
conn.commit()
#close the connection
conn.close()
