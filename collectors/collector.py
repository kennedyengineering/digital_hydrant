import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.global_config as gc

import sqlite3
import socket
import subprocess
import datetime
import yaml
import logging

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

        # create logger objects and configure
        self.logger = logging.getLogger("Digital Hydrant."+self.name)
        self.logger.setLevel(logging.DEBUG)
        self.fh = logging.FileHandler(gc.drive_path+"/"+gc.log_name)
        self.fh.setLevel(logging.DEBUG)
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)      # could also be ERROR or higher
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.fh.setFormatter(self.formatter)
        self.ch.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.ch)

        # for "self.execute", variables loaded from "config.yml"
        self.exec_duration = None
        self.enabled = None
        self.exec_time = None
        self.misc_config = {}

        # load YAML config file
        self.load_yaml()

        # try to establish connection to database
        # will throw error if USB drive is disconnected, do not proceed if there is not drive
        try:
            self.db_connection = sqlite3.connect(gc.drive_path + "/" + gc.db_name)
            self.cursor = self.db_connection.cursor()
        except Exception as err:
            self.logger.critical("Failed to init database connection: {}".format(err))
            exit()

    def load_yaml(self):
        self.logger.debug("Loading YAML config file")

        config_path = os.path.dirname(os.path.abspath(__file__))+"/{}/config.yml".format(self.name)

        # os check if file exists
        if not os.path.exists(config_path):
            self.logger.error("Config file: {} not found".format(config_path))
            return
        else:
            self.logger.debug("Config file: {} found".format(config_path))

        # parse the YAML config file
        self.logger.debug("Parsing {}".format(config_path))
        with open(config_path) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            try:
                self.exec_duration = data.pop("exec_duration", None)
                self.exec_time = data.pop("exec_time", None)
                self.enabled = data.pop("enabled", None)
                self.misc_config = data
            except KeyError as err:
                self.logger.error("Failed to parse {}, with error {}".format(config_path, err))
                return

        self.logger.debug("Parsed {}".format(config_path))

    def execute(self, cmd):

        command = str(cmd)

        if self.exec_duration != -1:
            command = "sudo timeout {} ".format(self.exec_duration) + command
        self.logger.debug("Executing {}".format(command))

        output = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

        return output

    def publish(self, dict):
        self.logger.debug("Publishing to table {}".format(self.name))

        date = str(datetime.datetime.now())

        keys, values = zip(*dict.items())

        table_columns = ''''''
        table_values = ''''''
        for key in keys:
            table_columns = table_columns + str(key) + " TEXT, "
            table_values = table_values + '"' + str(dict[key]) + '", '
        table_columns = table_columns + "DATETIME TIMESTAMP, UPLOADED INTEGER"
        table_values = table_values + '"' + date + '", 0'
        table_creation_cmd = "CREATE TABLE IF NOT EXISTS {} ({})".format(self.name, table_columns)
        table_insertion_cmd = "INSERT INTO {} VALUES({})".format(self.name, table_values)
        self.cursor.execute(table_creation_cmd)
        self.cursor.execute(table_insertion_cmd)
        self.db_connection.commit()
        self.__upload__(date)

    def __upload__(self, date):
        self.logger.debug("Uploading with datetime {}".format(date))

        # connect to queue server, notify daemon that entry is ready to be uploaded

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((gc.api_client_host, gc.api_client_port))
            payload = str(self.name) + ", " + str(date)
            s.sendall(bytes(payload, "utf-8"))

    def close(self):
        self.logger.debug("Closing out")
        self.db_connection.commit()
        self.db_connection.close()
