"""Debug provider module for Sitekick. This module is used to get information from a Linux server and send it to the
Sitekick server.
"""
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sitekick.config import SITEKICK_DEBUG_URL
from sitekick.utils import now, hostname, ip_address, mac_address, cli

EXECUTE_PARALLEL = False
DOMAIN_COUNT_PER_POST = 10  # Count and interval are optionally specified per module
DOMAIN_POST_INTERVAL = 1

def is_server_type():
    """Debugging, so always valid."""
    return True


def get_domains():
    """Get the intended info to retrieve. The command is retrieved from the Sitekick service, is retrieved according
    to the cron schedule, default every 5 minutes so commands can be changed and the result can be retrieved quite fast."""
    params = {'hostname': hostname or ip_address or mac_address}
    sitekick_url = SITEKICK_DEBUG_URL + '?' + urlencode(params)
    req = Request(sitekick_url, method='GET')
    # Get the list of commands, which is in the key 'command' in the json root of the request
    response = urlopen(req)
    data = json.loads(response.read())
    return data.get('commands', [])


def get_domain_info(domain):
    """The domain is not a string, but a command line request, as a list."""
    command = domain
    result = cli(command, include_stderr=True)
    return {'output': result}
