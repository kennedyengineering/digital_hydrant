#!/usr/bin/env python3

# network speed test collector utility, tests the upload/download speed of the network
# script will run through once, and store gathered data in the database
# command utility to scrape: speedtest-cli --simple
# gather information: ping, download, upload

################IMPORT STATEMENTS#################
import sqlite3
import os
import subprocess
import datetime
import sys
from modules.log import log

# load variables from config file
db_name = os.environ["db_name"]
drive_path = os.environ["drive_path"]
# connect to the SQLite3 database
conn = sqlite3.connect(str(drive_path) + "/" + str(db_name))
c = conn.cursor()
# check passed parameters
if len(sys.argv) != 2:
    log("timeout left undefined, exiting...", error=True)
    exit()
timeout = sys.argv[1]
##################################################

# create table if it does not exist
table_name = "speedtest"
c.execute('''CREATE TABLE IF NOT EXISTS {} (PING TEXT, DOWNLOAD TEXT, UPLOAD TEXT, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility
log("collecting data for table {}".format(table_name))
if timeout == "-1":     output = subprocess.run("speedtest-cli --simple", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
else:                   output = subprocess.run("sudo timeout {} speedtest-cli --simple".format(timeout), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

# parse the output into desired variables
output = output.split("\n")
ping = ''
download = ''
upload = ''
for entry in output:
    if entry.find("Ping") != -1:
        ping = entry
        ping = ping.split(": ")
        ping = ping[1]
    elif entry.find("Download") != -1:
        download = entry
        download = download.split(": ")
        download = download[1]
    elif entry.find("Upload") != -1:
        upload = entry
        upload = upload.split(": ")
        upload = upload[1]
#print(ping, download, upload)

# store to table:   # quotes were added to some strings to comply with SQL syntax
c.execute('''INSERT INTO {} VALUES("{}", "{}", "{}", "{}")'''.format(table_name, str(ping), str(download), str(upload), str(datetime.datetime.now())))

#commit the changes to the database
conn.commit()
#close the connection
conn.close()
