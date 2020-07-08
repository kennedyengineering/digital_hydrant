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
