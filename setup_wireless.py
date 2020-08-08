#!/usr/bin/env python3

import logging
import os
import config.global_config as gc
import subprocess

# setup wireless utility script
# ensures that all wireless interfaces are operational before launching Digital Hydrant


def setup_wireless():
    # create logger objects and configure
    logger = logging.getLogger("Digital Hydrant.setup.Wireless")
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

    if gc.enable_wireless:
        redo = True
        while redo:
            interface_name = subprocess.run('''iwconfig 2>&1 | grep -v "no wireless extensions" | grep -oP "^\w+"''', shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8").split("\n")
            interface_name.remove('')
            logger.debug("Found wireless interfaces: {}".format(str(interface_name)))

            activated_interface_name = subprocess.run('''ifconfig | grep -oP "^\w+"''', shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8").split("\n")
            activated_interface_name.remove('')
            logger.debug("Found activated network interfaces: {}".format(str(activated_interface_name)))

            redo = False
            for interface in interface_name:
                if interface in activated_interface_name:
                    logger.debug("Wireless interface {} is activated".format(interface))
                else:
                    logger.info("Wireless interface {} not activated, activating".format(interface))
                    os.system("sudo ifconfig {} up".format(interface))
                    redo = True
    else:
        logger.info("Enable wireless is disabled in the configuration, continuing")

    return 1
