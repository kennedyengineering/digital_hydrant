#!/usr/bin/env python3

# launcher for auth_tester.py, the actual collector

import yaml
import os

config_path = "config/wireless_network_credentials.yml"

# parse the YAML config file
with open(config_path) as f:
    data = yaml.load(f, Loader=yaml.FullLoader)

networks = data["networks"]
for credential in networks:
    essid = credential["essid"]
    passwd = credential["passwd"]
    os.system('collectors/wifi_auth/auth_tester.py "{}" "{}"'.format(essid, passwd))
