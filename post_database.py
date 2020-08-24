#!/usr/bin/env python3

import sqlite3
import sys
import re
import os
import subprocess
import time
from getmac import get_mac_address
import socket
import logging
import threading
import signal
import config.global_config as gc
import json

# create logger objects and configure
logger = logging.getLogger("Digital Hydrant.publisher")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(gc.drive_path + "/" + gc.log_name)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # could also be ERROR or higher
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


signal.signal(signal.SIGINT, signal_handler)
interrupted = False

# hydrant script to publish database tables to the web API

connection = sqlite3.connect(gc.drive_path+"/"+gc.db_name)
cursor = connection.cursor()
mac_addr = get_mac_address()
logger.info("Starting database API client")

HOST = gc.api_client_host
PORT = gc.api_client_port

api_token = ""
if not os.path.exists(gc.api_auth_token_path):
    logger.error("Authentication file: {} not found".format(gc.api_auth_token_path))
else:
    logger.debug("Authentication file: {} found".format(gc.api_auth_token_path))
    filesize = os.path.getsize(gc.api_auth_token_path)
    if filesize == 0:
        logger.error("Authentication file: {} empty".format(gc.api_auth_token_path))
    else:
        logger.debug("Authentication file: {} token found".format(gc.api_auth_token_path))
        api_token_file = open(gc.api_auth_token_path, "r")
        api_token = api_token_file.readline()
        api_token_file.close()

queue = []


def queue_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        while True:
            s.listen()
            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    queue.append(data.decode("utf-8"))


queue_thread = threading.Thread(target=queue_server, daemon=True)
queue_thread.start()

# select all un-uploaded data entries and add to queue
logger.debug("Scanning database for un-uploaded entries")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
table_names = cursor.fetchall()
for name in table_names:
    cursor.execute("SELECT DATETIME FROM {} WHERE UPLOADED = 0".format(name[0]))
    dates = cursor.fetchall() # returns a list of tuples with the data
    for date in dates:
        queue.append(name[0]+", "+date[0])

# main thread
while True:
    if len(queue) > 0:
        data = queue[0].split(", ")
        table_name = data[0]
        date = data[1]
        cursor.execute('select * from {} where DATETIME="{}"'.format(table_name, date))
        results = cursor.fetchall()
        names = list(map(lambda x: x[0], cursor.description))
        logger.debug("Processing data with datetime {}, uploading".format(str(date)))

        payload = '"{'
        for index in range(len(names)):
            name = '\\"'+str(names[index])+'\\"'+": "
            result = '\\"'+str(results[0][index])+'\\"'+", "
            payload = payload + name + result

        payload = payload[:-2] + '}"'

        cmd = '''curl -s -H "Authorization: Bearer {token}" -d '{"timestamp": {timestamp}, "type":"{table}", "source":"{mac_addr}", "payload":{payload}}' -H "Content-Type: application/json" -X POST https://digital-hydrant.herokuapp.com/v1 2>&1'''
        timestamp = int(round(time.time() * 1000))
        cmd = cmd.replace("{timestamp}", str(timestamp))
        cmd = cmd.replace("{table}", str(table_name))
        cmd = cmd.replace("{mac_addr}", str(mac_addr))
        cmd = cmd.replace("{payload}", str(payload))
        cmd = cmd.replace("{token}", str(api_token))
        raw_output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

        try:
            output = json.loads(raw_output)
            # get return value, and if it is zero, mark the database entry as a successful upload
            if "status" in list(output.keys()):
                logger.error("Failed to upload data with datetime {}, and output: {}".format(str(date), str(output)))     # server error
            else:
                logger.debug("Successfully uploaded data with datetime {}".format(str(date)))
                cursor.execute('UPDATE {} SET UPLOADED = 1 WHERE DATETIME="{}"'.format(table_name, date))               # no error
                connection.commit()

        except Exception as err:                                                                                        # local error
            logger.error("Data with datetime {} failed to upload with error: {}, and output: {}".format(date, err, raw_output))
            cursor.execute('UPDATE {} SET UPLOADED = 3 WHERE DATETIME="{}"'.format(table_name, date))   # uploaded = 3, means error, so it can be fixed later and won't try to be uploaded again
            connection.commit()

        del queue[0]

    if interrupted:
        logger.critical("Database API client interrupted, exiting")
        break

connection.close()

