import datetime
import socket
import subprocess
from uuid import getnode

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
try:
    mac_address = ':'.join(("%012X" % getnode())[i:i + 2] for i in range(0, 12, 2))
except:
    mac_address = None


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def cli(command):
    """Get the specified information form the specified end point on the local Plesk server using the CLI"""
    # In Python 3.6, you use stdout=PIPE to capture the output
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # The output is in bytes, so you must decode it to a string
        output_string = result.stdout.decode('utf-8')
        return output_string
    except FileNotFoundError:
        return None

