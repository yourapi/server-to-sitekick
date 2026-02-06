import datetime
import socket
import subprocess
import time
import hmac
import hashlib

from uuid import getnode

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
try:
    mac_address = ':'.join(("%012X" % getnode())[i:i + 2] for i in range(0, 12, 2))
except:
    mac_address = None


def now():
    return datetime.datetime.now().astimezone().isoformat()

def cli(command, include_stderr=False):
    """Execute the specified command as the current user from the command line interface (cli). Specify the command as
     a list with the arguments, the *popen args.
     Return the output as a string. Returns only stdout, if stderr is also needed, set include_stderr=True and both are
    returned as a tuple.
     """
    # In Python 3.6, you use stdout=PIPE to capture the output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # The output is in bytes, so you must decode it to a string
    if include_stderr:
        return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    else:
        return result.stdout.decode('utf-8')


def obfuscate(value: str, psk: str, *, length: int = 16) -> str:
    """
    Deterministic pseudonymization using HMAC-SHA256.
    Same (psk, value) -> same output. Different psk -> different mapping.

    length = number of bytes to keep from the digest (controls output size).
    Returns hex string (2*length chars).
    """
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    mac = hmac.new(psk.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
    return mac[:length].hex()