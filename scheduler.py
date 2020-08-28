#!/usr/bin/env python3

import os
from os import listdir
from os.path import isfile, isdir, join
import yaml
import time
import signal
import config.global_config as gc
import logging

# hydrant main program script, schedule and execute utilities according to configuration
# does not handle uploading to API

# create logger objects and configure
logger = logging.getLogger("Digital Hydrant.scheduler")
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


class Utility:
    # basic data type for holding information about the utility via parsing its config file
    # additional arguments and configuration can be added to config file, scheduler will only parse what it needs to run
    def __init__(self, util_path, config_path):
        self.logger = logging.getLogger("Digital Hydrant.scheduler.Utility")
        self.logger.debug("New Utility instance with parameters: {}, {}".format(util_path, config_path))

        self.util_path = util_path
    
        self.enabled = False
        self.exec_time = None
        self.exec_duration = None
        self.wireless = False

        self.load_yaml(config_path)

    # parse YAML config file
    def load_yaml(self, config_path):
        self.logger.debug("Parsing {}".format(config_path))
        with open(config_path) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            try:
                self.enabled = data["enabled"]
                self.exec_time = data["exec_time"]
                self.exec_duration = data["exec_duration"]
                self.wireless = data["wireless"]
                if gc.enable_wireless == False and self.wireless == True:
                    self.enabled = False
            except KeyError as err:
                self.logger.error("Failed to parse {}, with error {}".format(config_path, err))
                return

        self.logger.debug("Parsed {}".format(config_path))

    def execute(self):
        self.logger.debug("Executing {}".format(self.util_path))
        os.system(self.util_path)
        

class Scheduler:
    # Scheduler handles running utils according to their configurations
    def __init__(self, util_list):
        self.logger = logging.getLogger("Digital Hydrant.scheduler.Scheduler")

        self.util_list = util_list
        self.queue = util_list

    def execute_queue(self):
        # execute the next utility in the queue, then remove it from the queue
        if len(self.queue) != 0:
            util = self.queue[0]
            if util.enabled:
                exec_time = max(0, util.exec_time)          # make sure time is not negative, if it is it will be 0
                self.logger.debug("Waiting exec_time {}, for util {}".format(str(exec_time), util.util_path))
                time.sleep(exec_time)
                self.logger.info("Executing {}".format(util.util_path))
                util.execute()
            self.queue.remove(util)


logger.info("Starting Scheduler")

# load collector directory path names
# directories to be not added to the collector dir list
dir_blacklist = ['__pycache__', 'speedtest', 'hydra', 'nmap', 'lldp', 'netdiscover', 'wifi_auth', 'wifi_quality', 'dhcp']
#dir_blacklist = ['__pycache__']

dir_list = [f for f in listdir("collectors") if isdir(join("collectors", f)) and f not in dir_blacklist]

# create utility objects
utility_list = []
for dir in dir_list:
    main = "collectors/"+dir+"/main.py"
    config = "collectors/"+dir+"/config.yml"
    utility_list.append(Utility(main, config))

scheduler = Scheduler(utility_list)
while 1:
    scheduler.execute_queue()
    if interrupted:
        logger.critical("Main loop interrupted, exiting")
        break
