#!/usr/bin/env python3

# DHCP collector utility, record dynamic host configuration protocol data
# script will run through once, and store gathered data in the database
# command utility to scrape: sudo dhcpcd -T {interface (optional)}
# gather information: all DHCP information--log

################IMPORT STATEMENTS#################
import sqlite3
import os
import subprocess
import datetime

# load variables from config file
db_name = os.environ["db_name"]
drive_path = os.environ["drive_path"]
# connect to the SQLite3 database
conn = sqlite3.connect(str(drive_path) + "/" + str(db_name))
c = conn.cursor()
##################################################

# create table if it does not exist
table_name = "dhcp"
c.execute('''CREATE TABLE IF NOT EXISTS {} (DHCP_LOG TEXT, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility
print("collecting data for table {}".format(table_name))
output = subprocess.run("sudo dhcpcd -T", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

# parse the output into desired variables

# store to table:   # quotes were added to some strings to comply with SQL syntax
c.execute('''INSERT INTO {} VALUES("{}", "{}")'''.format(table_name, output, str(datetime.datetime.now())))

#commit the changes to the database
conn.commit()
#close the connection
conn.close()

