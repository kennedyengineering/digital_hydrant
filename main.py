#!/usr/bin/env python3

import config.global_config as gc
import os
import setup_usb as usb
import setup_wireless as wifi
import logging

# main launcher for Digital Hydrant
# configure hardware and then launch the software

usb_status = usb.setup_usb()
if usb_status == 0:
	exit()

wifi_status = wifi.setup_wireless()
if wifi_status == 0:
	exit()

# create logger objects and configure
logger = logging.getLogger("Digital Hydrant")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(gc.drive_path + "/output.log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # could also be ERROR or higher
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

logger.info("Starting Digital Hydrant")

logger.debug("Launching Publisher daemon")
# ./post_database.py &
logger.debug("Launching Scheduler")
# ./scheduler.py
