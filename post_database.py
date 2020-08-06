#!/usr/bin/env python3

import sqlite3
import sys
import re
import os
import time
from getmac import get_mac_address
import socket
import logging
import threading
import signal
import config.global_config as gc

# create logger objects and configure
logger = logging.getLogger("Digital Hydrant.publisher")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(gc.drive_path + "/output.log")
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

HOST = os.environ["api_client_host"]
PORT = int(os.environ["api_client_port"])

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

# main thread
while True:
    if len(queue) > 0:
        data = queue[0].split(", ")
        table_name = data[0]
        date = data[1]
        cursor.execute('select * from {} where DATETIME="{}"'.format(table_name, date))
        results = cursor.fetchall()
        names = list(map(lambda x: x[0], cursor.description))
        logger.debug("Received data with datetime {}, uploading".format(str(date)))

        payload = '"{'
        for index in range(len(names)):
            name = '\\"'+str(names[index])+'\\"'+": "
            result = '\\"'+str(results[0][index])+'\\"'+", "
            payload = payload + name + result

        payload = payload[:-2] + '}"'

        cmd = '''curl -s -d '{"timestamp": {timestamp}, "type":"{table}", "source":"{mac_addr}", "payload":{payload}}' -H "Content-Type: application/json" -X POST https://digital-hydrant.herokuapp.com/v1 > /dev/null'''
        timestamp = time.time()
        cmd = cmd.replace("{timestamp}", str(timestamp))
        cmd = cmd.replace("{table}", str(table_name))
        cmd = cmd.replace("{mac_addr}", str(mac_addr))
        cmd = cmd.replace("{payload}", str(payload))
        os.system(cmd)

        del queue[0]

    if interrupted:
        logger.critical("Database API client interrupted, exiting")
        break

connection.close()
