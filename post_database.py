#!/usr/bin/env python3

import sqlite3
import sys
import re
import os
import time
from getmac import get_mac_address

# hydrant script to publish all database tables to the web API
# time intensive, just for testing purposes
# will be adapted into a system enabling dynamic updates to the API

print("Dumping database to web API")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

connection = sqlite3.connect("/media/USBDrive/hydrant.db")
connection.row_factory = dict_factory

cursor = connection.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for name in tables:
    table = name["name"]
    
    cursor.execute("select * from {}".format(table))
    results = cursor.fetchall()

    mac_addr = get_mac_address()

    for entry in results:
        result = str(entry)
        result = re.sub("'", '\\"', result)
        timestamp = time.time()
        cmd = '''curl -d '{"timestamp": {timestamp}, "type":"{table}", "source":"{mac_addr}", "payload":"%s"}' -H "Content-Type: application/json" -X POST https://digital-hydrant.herokuapp.com/v1 > /dev/null'''
        cmd = cmd.replace("{timestamp}", str(timestamp))
        cmd = cmd.replace("{table}", str(table))
        cmd = cmd.replace("{mac_addr}", str(mac_addr))
        cmd = cmd % result
        os.system(cmd)

connection.close()
