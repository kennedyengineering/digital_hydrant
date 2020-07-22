#!/usr/bin/env python3

import datetime
import os
from os import listdir
from os.path import isfile, join
import yaml

# hydrant main program script, schedule and execute utilities according to configuration
# does not handle uploading to API
# run in the background

print("[INFO] Starting Digital Hydrant", datetime.datetime.now())

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

for i in utility_config_dict:
    f = utility_config_dict[i]
    print(f)
    with open("utils/config/"+f) as ff:
        data = yaml.load(ff, Loader=yaml.FullLoader)
        print(data)

#for utility in utility_files:
#    os.system("utils/"+utility)
