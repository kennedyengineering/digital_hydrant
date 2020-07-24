#!/usr/bin/env python3

import sqlite3
import sys
import re
import os
import time
from getmac import get_mac_address
import socket
from utils.modules.log import log
import threading
import signal

def signal_handler(signal, frame):
    global interrupted
    interrupted = True
signal.signal(signal.SIGINT, signal_handler)
interrupted = False

# hydrant script to publish database tables to the web API

connection = sqlite3.connect("/media/USBDrive/hydrant.db")
cursor = connection.cursor()
mac_addr = get_mac_address()
log("Starting database API client")

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

        payload = '"{'
        for index in range(len(names)):
            name = '\\"'+str(names[index])+'\\"'+": "
            result = '\\"'+str(results[0][index])+'\\"'+", "
            payload = payload + name + result

        payload = payload[:-2] + '}"'

        cmd = '''curl -d '{"timestamp": {timestamp}, "type":"{table}", "source":"{mac_addr}", "payload":{payload}}' -H "Content-Type: application/json" -X POST https://digital-hydrant.herokuapp.com/v1 > /dev/null'''
        timestamp = time.time()
        cmd = cmd.replace("{timestamp}", str(timestamp))
        cmd = cmd.replace("{table}", str(table_name))
        cmd = cmd.replace("{mac_addr}", str(mac_addr))
        cmd = cmd.replace("{payload}", str(payload))
        os.system(cmd)

        del queue[0]

    if interrupted:
        log("Stopping database API client", error=True)
        break

connection.close()
