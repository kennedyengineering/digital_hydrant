#!/usr/bin/env python3

# hydrant utility, lldp - Link Layer Discovery Protocol, search for LLDP neighbors, get information on switches
# script will run through once, and store gathered data in the database
# command utility to scrape: lldpctl (-f json?)
# gather information: SysName, SysDescr, PortID, MgmtIP, vlan-id

################IMPORT STATEMENTS#################
import sqlite3
import os
import subprocess
import datetime
import json     # the module being parsed output JSON format, use module to make life easier
from modules.log import log
import sys

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
table_name = "lldp"
c.execute('''CREATE TABLE IF NOT EXISTS {} (SYSTEM_NAME TEXT, SYSTEM_DESCRIPTION TEXT, PORT_ID TEXT, MANAGEMENT_IP TEXT, VLAN_ID INTEGER, DATETIME TIMESTAMP)'''.format(table_name))

# scrape the command line utility   # netdiscover either runs indefinetely or just a really long time, a timeout is needed, set in seconds
log("collecting data for table {}".format(table_name))
if timeout == "-1":     output = subprocess.run("lldpctl -f json", shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
else:                   output = subprocess.run("sudo timeout {} lldpctl -f json".format(timeout), shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

# parse the output into desired variables
output = json.loads(output)
try:
    for i in output["lldp"]["interface"]:   # iterate per interface
        # SysName
        sysname = list(output["lldp"]["interface"][i]["chassis"].keys())[0]
        #print(sysname)

        # SysDescr
        sysdescr = output["lldp"]["interface"][i]["chassis"][sysname]["descr"]
        #print(sysdescr)
       
        # PortID
        portid = output["lldp"]["interface"][i]["port"]["id"]["type"]
        portid += " " + output["lldp"]["interface"][i]["port"]["id"]["value"]
        #print(portid)

        # MgmtIP
        mgmtip = output["lldp"]["interface"][i]["chassis"][sysname]["mgmt-ip"]
        #print(mgmtip)

        # vlan-id
        vlanid = int(output["lldp"]["interface"][i]["vlan"]["vlan-id"])
        #print(vlanid, type(vlanid))

        # store to table:   # quotes were added to some strings to comply with SQL syntax
        c.execute('''INSERT INTO {} VALUES({}, {}, {}, {}, {}, {})'''.format(table_name, '"'+str(sysname)+'"', '"'+str(sysdescr)+'"', '"'+str(portid)+'"', '"'+str(mgmtip)+'"', vlanid, '"'+str(datetime.datetime.now())+'"'))

except KeyError:
    log("no interface found", error=True)

#commit the changes to db			
conn.commit()
#close the connection
conn.close()
