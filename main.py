#!/usr/bin/env python3

import config.global_config as gc
import os
import setup_usb as usb
import setup_wireless as wifi
import logging
import subprocess
import signal


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


signal.signal(signal.SIGINT, signal_handler)
interrupted = False

# main launcher for Digital Hydrant
# configure hardware and then launch the software

if gc.enable_drive:
    usb_status = usb.setup_usb()
    if usb_status == 0:
        exit()
else:
    gc.drive_path = os.path.dirname(os.path.realpath(__file__))

wifi_status = wifi.setup_wireless()
if wifi_status == 0:
    exit()

# create logger objects and configure
logger = logging.getLogger("Digital Hydrant")
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

logger.info("Starting Digital Hydrant")

logger.debug("Launching Publisher daemon")
# ./post_database.py &
publisher = subprocess.Popen("./post_database.py", shell=True, stdout=subprocess.PIPE)

logger.debug("Launching Scheduler")
# ./scheduler.py
scheduler = subprocess.Popen("./scheduler.py", shell=True, stdout=subprocess.PIPE)

while 1:
    if interrupted:
        logger.critical("Main loop interrupted, exiting")
        break

