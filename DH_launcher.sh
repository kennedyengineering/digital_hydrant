#!/bin/bash

# Digital Hydrant 2020
# DH_launcher.sh is a bash script used for development purposes
# production releases should execute main.py
# the purpose of this script is to kill all child processes that are not handled by main.py
# useful for prematurely stopping the program and not leaving behind running processes

trap "kill 0" EXIT

./main.py
