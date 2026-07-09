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

    result = [["plesk", "version"],
            ["plesk", "bin", "site", "--list"],
            ["plesk", "bin", "domain", "--info", "sitekick.eu"],
            ["plesk", "db", "-sNe",
             "SELECT d.name, h.php_handler_id FROM domains d JOIN hosting h ON h.dom_id=d.id WHERE d.name='sitekick.eu'"],
            ["echo", hostname]]
    params = {'hostname': hostname or ip_address or mac_address}
    sitekick_url = SITEKICK_DEBUG_URL + '?' + urlencode(params)
    req = Request(sitekick_url, method='GET')
    # Get the list of commands, which is in the key 'command' in the json root of the request
    response = urlopen(req)
    data = json.loads(response.read())
    result = data.get('commands', [])
    return [repr(item) for item in result]


def get_domain_info(domain):
    """The domain is not a string, but a command line request, as a list."""
    command = eval(domain)
    result = cli(command, include_stderr=True)
    return {'output': result}
