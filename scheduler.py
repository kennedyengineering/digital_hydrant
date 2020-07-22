#!/usr/bin/env python3

import datetime

# hydrant main program script, schedule and execute utilities according to configuration
# does not handle uploading to API
# run in the background

print("[INFO] Starting Digital Hydrant", datetime.datetime.now())

import os
from os import listdir
from os.path import isfile, join
utility_files = [f for f in listdir("utils") if isfile(join("utils", f)) and f[-3:]==".py"]

for utility in utility_files:
    os.system("utils/"+utility)
