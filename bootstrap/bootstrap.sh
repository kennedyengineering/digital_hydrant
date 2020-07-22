#!/bin/bash

# install dependencies listed in requirement files

sudo apt update
sudo apt install -y $(cat apt_package_list)

pip3 install -r pip_package_list
