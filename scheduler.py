#!/usr/bin/env python3

import os
from os import listdir
from os.path import isfile, isdir, join
import yaml
import time
import signal

# hydrant main program script, schedule and execute utilities according to configuration
# does not handle uploading to API

def signal_handler(signal, frame):
    global interrupted
    interrupted = True
signal.signal(signal.SIGINT, signal_handler)
interrupted = False

class Utility:
    # basic data type for holding information about the utility via parsing its config file
    # additional arguments and configuration can be added to config files, scheduler will only parse what it needs to run
    def __init__(self, util_path, config_path):
        self.util_path = util_path
    
        self.enabled = False
        self.exec_time = None
        self.exec_duration = None

        self.load_yaml(config_path)

    # parse YAML config file
    def load_yaml(self, config_path):
        print("parsing "+config_path)
        with open(config_path) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            try:
                self.enabled = data["enabled"]
                self.exec_time = data["exec_time"]
                self.exec_duration = data["exec_duration"]
            except KeyError:
                print("failed to parse "+config_path)

    def execute(self):
        print("executing "+self.util_path)
        os.system(self.util_path)
        

class Scheduler:
    # Scheduler handles running utils according to their configurations
    def __init__(self, util_list):
        self.util_list = util_list
        self.queue = util_list

    def execute_queue(self):
        # execute the next utility in the queue, then remove it from the queue
        if len(self.queue) != 0:
            util = self.queue[0]
            if util.enabled:
                exec_time = max(0, util.exec_time)          # make sure time is not negative, if it is it will be 0
                print("waiting exec_time "+str(exec_time))
                time.sleep(exec_time)
                util.execute()
            self.queue.remove(util)

print("starting Digital Hydrant")

# load collector directory path names
# directories to be not added to the collector dir list
dir_blacklist = ['__pycache__', 'wifi_quality', 'speedtest', 'netdiscover', 'wifi_auth', 'lldp', 'auth_nearest_wifi', 'collector_template']
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
        print("main loop interrupted, exiting...")
        break
