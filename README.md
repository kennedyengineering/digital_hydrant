"dependencies"
# for setting up USB encryption
# instructions from: https://linux.tips/tutorials/how-to-encrypt-a-usb-drive-on-linux-operating-system
- shred
- cryptsetup
- wireless-tools
- iw
- sqlite3

"development notes"
- After completing software, make SD card a readonly filesystem for stability. Use usb drive for storing logs
- setup_usb is a script for managing the encrypted volume, give device path "EX: /dev/sda" and operation "create, unmount, mount" running with sudo is not required
- wifi interface may not be visible by "ifconfig", find interface name with "iwconfig", and then "ifconfig <interface> up"
- interactive SQL prompt with bash command "sqlite3"
- using SQLite3 because it is file/disk based and will be easier to use on the USB drive
- the utils directory will be populated with tasks, with the purpose of independently gathering, parsing, and then storing data upon execution of the script
