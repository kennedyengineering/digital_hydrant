#!/usr/bin/env python3

# Digital Hydrant 2020
# setup_usb.py is the python equivallent of the bash script setup_usb.sh
# its purpose is to automate the discovery, mounting, formating, and encryption/decryption of USB mass storage drives
# the USB drive will then be usable by Digital Hydrant for storing database and log files
# the main function, setup_usb(), can be called by itself to allow developers easy access the USB drive 

import os
import config.global_config as gc
import subprocess

def setup_usb():
    # main method
    print("Digital Hydrant.setup.USB Starting setup")
    drive = subprocess.run('''lsblk | grep "{}"'''.format(gc.drive_name), shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    if drive:
        print("Digital Hydrant.setup.USB Drive {} found".format(gc.drive_name))
        mounted = subprocess.run('''lsblk | grep "{}"'''.format(gc.drive_path), shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
        if mounted:
            print("Digital Hydrant.setup.USB Drive {} mounted".format(gc.drive_name))
        else:
            print("Digital Hydrant.setup.USB Drive {} not mounted, mounting".format(gc.drive_name))
            return mount()
    else:
        print("Digital Hydrant.setup.USB Drive {} not found".format(gc.drive_name))
        return 0

    print("Digital Hydrant.setup.USB Setup complete")
    return 1


def mount():
    print("Digital Hydrant.setup.USB Mounting drive {} on {} using luks key {}".format(gc.drive_name, gc.drive_path, gc.luks_key_filename))
    output = subprocess.run("sudo cryptsetup luksOpen {} USBDrive --key-file=$PWD/{}  2>&1".format("/dev/"+gc.drive_name, gc.luks_key_filename), shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")

    if output == "No key available with this passphrase.\n" or output == "Failed to open key file.\n":
        print("Digital Hydrant.setup.USB Failed to unlock drive {} using luks key {}".format(gc.drive_name, gc.luks_key_filename))
        return create()
    else:
        os.system("sudo mount /dev/mapper/USBDrive {}".format(gc.drive_path))
        print("Digital Hydrant.setup.USB Mounted drive {}".format(gc.drive_name))
        return 1


def unmount():
    print("Digital Hydrant.setup.USB Unmounting drive {}".format(gc.drive_name))
    os.system("sudo umount {}".format(gc.drive_path))
    os.system("sudo cryptsetup luksClose USBDrive")
    print("Digital Hydrant.setup.USB Unmounted drive")


def create(secure_erase=False):
    if secure_erase:
        print("Digital Hydrant.setup.USB Securely erasing drive {}".format(gc.drive_name))
        os.system("sudo shred -v -n 1 {}".format("/dev/"+gc.drive_name))
        print("Digital Hydrant.setup.USB Erased drive")

    unmount()

    print("Digital Hydrant.setup.USB Creating new encrypted drive")
    os.system("dd if=/dev/urandom of=$PWD/{} bs=512 count=8".format(gc.luks_key_filename))
    os.system("sudo cryptsetup -q luksFormat {} --key-file=$PWD/{}".format("/dev/"+gc.drive_name, gc.luks_key_filename))
    os.system("sudo cryptsetup luksOpen {} USBDrive --key-file=$PWD/{}".format("/dev/"+gc.drive_name, gc.luks_key_filename))
    os.system("sudo mkfs -t ext4 /dev/mapper/USBDrive")

    if not os.path.exists(gc.drive_path):
        os.system("sudo mkdir {}".format(gc.drive_path))

    os.system("sudo mount /dev/mapper/USBDrive {}".format(gc.drive_path))
    os.system("sudo chown $USER {}".format(gc.drive_path))
    print("Digital Hydrant.setup.USB Created new encrypted drive")

    return 1
