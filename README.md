<a href="http://outsideopen.com"><img src="https://cdn.pixabay.com/photo/2017/06/27/20/24/fire-hydrants-2448725_960_720.png" title="Outside Open" alt="Outside Open"></a>

# Digital Hydrant Collectors

> Open Source network information collector, developed for the Digital Hydrant project

![Build Status](http://img.shields.io/travis/badges/badgerbadgerbadger.svg?style=flat-square) [![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)


## Table of Contents

- [Installation](#installation)
- [Features](#features)
- [Contributing](#contributing)
- [Team](#team)
- [FAQ](#faq)
- [Support](#support)
- [License](#license)


---

## Installation

- All the code required to get started is in this repository
- Execute the `bootstrap/bootstrap.sh` to install dependencies
- Allow passwordless `sudo` on your [user](https://timonweb.com/devops/how-to-enable-passwordless-sudo-for-a-specific-user-in-linux/)

### Clone

- Clone this repo to your local machine using `https://github.com/outsideopen/digital-hydrant-collectors`

### Setup

> clone this repository

```shell
$ git clone https://github.com/outsideopen/digital-hydrant-collectors.git
```

> `cd` into the base directory

```shell
$ cd ~/digital-hydrant-collectors
```

> run the bootstrap script

```shell
$ ./bootstrap/bootstrap.sh
```

> create an API token on the Digital Hydrant [website](https://digital-hydrant.herokuapp.com/login)
>
> store API token in file `api_token`

```shell
$ <your_token> > api_token
```

> view `config/global_config.py` and configure desired runtime behaviour

```shell
$ vim config/global_config.py
```

> view `collectors/<collector_name>/config.yml` and configure desired runtime behaviour

```shell
$ vim collectors/<collector_name>/config.yml
```

> (optional) plug in a USB mass storage device

> start Digital Hydrant

```shell
$ ./DH_launcher.sh
```

---

## Features

- Easily add new collectors
- Build off existing network scanning tools
- Integrated logging
- Very flexible and configurable

## Develpment Notes

- After completing software, make SD card a readonly filesystem for stability. Use usb drive for storing logs
- setup_usb is a script for managing the encrypted volume, give device path "EX: /dev/sda" and operation "create, unmount, mount" running with sudo is not required
- wifi interface may not be visible by "ifconfig", find interface name with "iwconfig", and then "ifconfig <interface> up"
- interactive SQL prompt with bash command "sqlite3"
- using SQLite3 because it is file/disk based and will be easier to use on the USB drive
- the utils directory will be populated with tasks, with the purpose of independently gathering, parsing, and then storing data upon execution of the script
- utilities were originally written in bash but moved to python equivalent scripts due to python supporting sqlite3 natively and having far superior string manipulating capabilities
- the python scripts cannot be run independently of the main program due to it relying on environment variables being exported in "config" file
- sqlitebrowser is an opensource sqlite GUI, works well for visualizing data entry and works well over SSH X-forwarding
- lldpd is the daemon/service, after installing should be activated with "service lldpd start"
- netplan is used to configure wifi on ubuntu 20.04, this link should help: https://linuxconfig.org/ubuntu-20-04-connect-to-wifi-from-command-line
- netplan abstracts to "systemd-networkd" (ubuntu server 20.04)
- you can avoid using netplan by just using wpa_supplicant
- closing wpa_supplicant prematurely can leave an extra interface listing in "iw dev" which can be removed by bringing the physical interface (wlan0) "down" and back "up" with ifconfig
- iperf is used for measuring network bandwith, on one computer run "iperf -s" to start server, and on the client run "iperf -c <IP_ADDRESS> -n <size>M" to connect to server and request payload of specified size in Megabytes
- testing the Raspberry Pi 4 with iperf shows that it has a 62.5 Mbit/sec wireless bandwidth when connected to a 5GHZ network
- speedtest-cli is a command for measuring internet upload and download speeds, use "speedtest-cli" to see results
- created a collector template file in the utility directory, can be copied and pasted and modified to create new utilities easier
- "main" does not need to be run as sudo, but the user executing it needs to have passwordless sudo enabled
- created a bootstrap directory for setting up the project upon installation, for a more up to date versioon of dependencies view the requirements files, will stop tracking in the README.md
- /media/USBdrive is created when "create" option of setup_usb is run, so the setup_usb script must be run upon a new installation
- utils/config contains the config file for the corresponding collector, the names must match for scheduler.py to pick them up and use them. The config files all contain information about scheduling and execution duration (timeout setting in seconds), can contain additional information for use in the collector
- scheduler.py is the "launcher" for the collectors, it creates a queue and then executes them
- config/wireless_network_credentials.yml contains wireless network information for authentication collectors
- created utils/modules to store helper functions and limit code repitition
- data is sent to the web API via the post_database.py daemon. It runs in the background and is entirely self contained in main. It acts as a server, whose hostname and port are configurable in "config/bash_config". That configuration data is also used in the module upload.py, which acts as a client and sends data to post_database.py. It sends the table name and date as identifiers and post_database.py adds it to a queue to be uploaded. the "upload" method should be called whenever there is an insertion operation on the database. The thing to be warned of is the date passed through the method should be the same as listed in the database entry
- it is necessary and a good precaution to add the Sqlite connection commit command to avoid the upload function from returning no matches when quereying the database
- project structure has been reorganized! Each collector is a directory containing atleast main.py and config.yml. Scheduler will automatically find the collectors and execute them according to their configuration file.
- collector.py handles to repetitive code, and easily standardizes interfacing to the Digital Hydrant system. It automatically creates SQL tables based on input data, handles uploading, and logging.
- see dhcp collector for a template, removed collector_template directory
- From Tjaart: The process to create a token:
    - Log into the web interface
    - Browse to: https://digital-hydrant.herokuapp.com/manage/tokens
    - Click "Generate Token", and copy the resulting token
    - Add the token to your request. I updated the example in the wiki to reflect the change https://github.com/outsideopen/digital-hydrant-server/wiki/Digital-Hydrant-API#example
- added API token to base level of project directory, in file called api_token, single line. If file name/path changes edit the config files
- uploading in JSON format, curl does not like payloads with newline characters. Use the bash command "tr '/n' ' '" to convert newline to spaces, etc or in python use "<string>.replace('\n', ' ')"
- use 2> to redirect stderr output
- wifi_auth/auth_tester.py has trouble when multiple wireless interfaces are available. Does not work

## To Do

- test for vulnerabilities and crashes. Wifi auth_tester is vulnerable with multiple wireless interfaces, Early interrupt signal does not kill all child processes (used to have trap?)
- fix \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 type ESSID in wifi_quality, \x00 is a null character so something it messed up with the parsing
- modify the upload method to allow \ with out errors
- replace bash scripts looking for interfaces with python [module](https://pypi.org/project/netifaces/)
- create another daemon to remove entries inserted at a specified time interval
- add package management system to bootstrap (pipfile? setuptools? docker image?)
---

## Contributing
### Step 1

- **Option 1**
    - 🍴 Fork this repo!

- **Option 2**
    - 👯 Clone this repo to your local machine using `https://github.com/outsideopen/digital-hydrant-collectors`

### Step 2

- **HACK AWAY!** 🔨🔨🔨

### Step 3

- 🔃 Create a new pull [request](https://github.com/outsideopen/digital-hydrant-collectors/compare)

---

## Team

> Contributors

| <a href="https://github.com/kennedyengineering" target="_blank">**kennedyengineering**</a> 
| :---: |
| [![kennedyengineering](https://avatars2.githubusercontent.com/u/31577746?s=200)](http://github.com/kennedyengineering)
| <a href="http://github.com/kennedyengineering" target="_blank">`github.com/kennedyengineering`</a>

---

## FAQ

- Outside Open is a team of smart, passionate artists, photographers, cyclists, hikers, soccer players, parents, beekeepers, blacksmiths and tinkerers. What unites this disparate team is a love for building and integrating amazing technology to help their clients succeed.  They think outside the “singular technical solution” box.  They embrace solutions from both the standard corporate software/hardware world and the open source community.  This sets them apart and enables them to provide highly customized and scaleable solutions. Outside Open was founded in 2012 by Trevor Young and Greg Lawler, two technology leaders with a love for technology and a desire to help others succeed.

---

## Support

Reach out at one of the following places!

- Website at <a href="http://outsideopen.com" target="_blank">`outsideopen.com`</a>

---

## License

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)

- **[MIT license](http://opensource.org/licenses/mit-license.php)**
