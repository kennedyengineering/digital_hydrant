"dependencies"
# for setting up USB encryption
# instructions from: https://linux.tips/tutorials/how-to-encrypt-a-usb-drive-on-linux-operating-system
- shred
- cryptsetup
- wireless-tools
- egrep 
- sqlite3
- netdiscover
- lldpd
- iw
- wpasupplicant
- speedtest-cli
- iperf

"development notes"
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
