#!/bin/bash

# Digital Hydrant 2020
# bootstrap.sh installs packages required for Digital Hydrant to run
# it install dependencies listed in requirement files: apt_package_list, pip_package_list

sudo apt update
sudo apt install -y $(cat apt_package_list)

pip3 install -r pip_package_list
