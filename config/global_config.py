# Digital Hydrant 2020
# replacement to bash_config
# sets global variables related to the system and desired runtime behavior
import os

enable_drive = False

drive_name = "sda"		            # can find using "lsblk"
luks_key_filename = "luks_key"      # filename of the luks_key

drive_path = "/media/USBDrive"	    # mounting point for the drive
if not enable_drive:
    drive_path = str(os.path.dirname(os.path.realpath(__file__)))+"/temp"

db_name = "hydrant.db"	            # name of sqlite3 database, located on USB drive
log_name = "output.log"

api_auth_token_path = "api_token"   # the path to the text file containing the API auth token for uploading to the web interface
api_client_port = 65432		        # Standard loopback interface address (localhost)
api_client_host = "127.0.0.1"	        # Port to listen on (non-privileged ports are > 1023)

enable_wireless = True                # enable use of wireless interfaces
