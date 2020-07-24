
# post the minimum amount of data to a queue file "temp/queue" in order for the entry to be found and uploaded
# datetime must be the exact same datetime as the one in the data entry
# queue file is in CSV format

import os
import socket

HOST = os.environ["api_client_host"]
PORT = int(os.environ["api_client_port"])

def upload(table_name, datetime):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        payload = str(table_name) + ", " + str(datetime)
        s.sendall(bytes(payload, "utf-8"))

