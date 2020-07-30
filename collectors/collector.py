import config.global_config
import sqlite3
import socket
import subprocess
import datetime
import yaml

# Collector object class definition
# contains all the base functions needed for interfacing with the Digital Hydrant system
# used for reducing code repetitiveness and consolidating code
# all scraping and data processing will be done in the collector's "main.py"
# will handle loading configuration data from the collector's "config.yml"
# will handle logging information, printing colored output, and saving to file

class Collector:
    def __init__(self, name):
        # create all variables
        self.name = str(name)

        # for "self.execute"
        self.exec_time = None
        # for ??scheduler.py?? or have it load itself?
        self.exec_duration = None
        self.enabled = False

        # try to establish connection to database
        # will throw error if USB drive is disconnected, do not proceed if there is not drive
        try:
            self.db_connection = sqlite3.connect(drive_path + "/" + db_name)
            self.cursor = self.connection.cursor()
        except:
            # logging.critical note cannot establish connection to database
            exit()

        # if wireless is enabled, make sure it is working before proceeding
        if wireless_is_enabled:
            # run checks
            pass

    def load_yaml(self):
        # load "config.yml"
        # in directory with name matching "self.name"
        # load timeout
        # load other misc arguments into a dict
        pass

    def execute(self, cmd):
        # takes command as a string
        # load timeout from YAML, append to command
        # execute using subprocess
        # return captured output
        pass

    def publish(self, args):
        # create table [if not exists] using type detection of passed arguments/variables
        # insert into table
        # connection commit
        # self.upload
        pass

    def __upload__(self, table_name, datetime):
        # connect to queue server, notify daemon that entry is ready to be uploaded

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((api_client_host, api_client_port))
            payload = str(self.name) + ", " + str(datetime)
            s.sendall(bytes(payload, "utf-8"))

    def __del__(self):
        self.db_connection.commit()
        self.db_connection.close()

