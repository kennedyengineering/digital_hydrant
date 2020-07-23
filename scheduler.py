#!/usr/bin/env python3

from utils.modules.log import log
import os
from os import listdir
from os.path import isfile, join
import yaml
import time
import signal

# hydrant main program script, schedule and execute utilities according to configuration
# does not handle uploading to API
# run in the background

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
        log("parsing "+config_path)
        with open("utils/config/"+config_path) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            try:
                self.enabled = data["enabled"]
                self.exec_time = data["exec_time"]
                self.exec_duration = data["exec_duration"]
            except KeyError:
                log("failed to parse "+config_path, error=True)

    def execute(self):
        log("executing "+self.util_path)
        os.system("utils/"+self.util_path+" "+str(self.exec_duration))
        

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
                util.execute()
                exec_time = max(0, util.exec_time)          # make sure time is not negative, if it is it will be 0
                log("waiting exec_time "+str(exec_time))
                time.sleep(exec_time)
            self.queue.remove(util)

log("starting Digital Hydrant")

# load file names
utility_files = [f for f in listdir("utils") if isfile(join("utils", f)) and f[-3:]==".py"]
utility_config = [f for f in listdir("utils/config") if isfile(join("utils/config", f)) and f[-4:]==".yml"]

# match python file to config file
# could just assume they have the same filename and catch exceptions, but this filters out files without a matching python/config pair
utility_config_dict = {}
for f in utility_files:
    f_compare = f.replace(f[-3:], '')
    for ff in utility_config:
        ff_compare = ff.replace(ff[-4:], '')
        if f_compare == ff_compare:
            utility_config_dict[f] = ff

utility_list = []
for i in utility_config_dict:
    f = utility_config_dict[i]
    utility_list.append(Utility(i, f))

scheduler = Scheduler(utility_list)
while 1:
    scheduler.execute_queue()
    if interrupted:
        log("main loop interrupted, exiting...", error=True)
        break
