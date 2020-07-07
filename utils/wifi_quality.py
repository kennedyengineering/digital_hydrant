#!/usr/bin/env python3

# hydrant utility, search for nearby wireless accesspoints
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID'

import sqlite3
import os

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
    # create table

			
#commit the changes to db			
conn.commit()
#close the connection
conn.close()
