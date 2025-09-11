"""This template outlines a provider for the server-to-sitekick code. Copy this file to a new file in the providers
directory, and change the functions to suit your needs. The functions are:
is_server_type()    Returns True-ish if the server on which the server is running, is of the appropriate type.
                    Returns False-ish or raise an error if not the specified type, so you can just call any function
                    to determine whether the server is of the appropriate type.
get_domains()       Get all domains from the local hosting server. Return a complete list of domain names.
get_domain_info()   Get detailed information about the specified domain from the local hosting server.
                    Return a dictionary with the domain info. The domain name is added to the dictionary under the
                    key 'domain'. When additional or different info is needed, change this function.

It can also contain a number of optional constants, which can be used to change the behaviour of the server-to-sitekick
code. The constants are:
EXECUTE_PARALLEL        Whether to execute the get_domains_info() and push_domains_info() calls in parallel. True when
                        not specified.
DOMAIN_COUNT_PER_POST   Number of detailed domain info packages to send per post. Defaults to
                        sitekick.send.DOMAIN_COUNT_PER_POST
DOMAIN_POST_INTERVAL    Seconds, interval between posts. Defaults to sitekick.send.DOMAIN_POST_INTERVAL
"""
from sitekick.utils import now, hostname, ip_address, mac_address

EXECUTE_PARALLEL = False
DOMAIN_COUNT_PER_POST = 100
DOMAIN_POST_INTERVAL = 1

def is_server_type():
    """Returns True-ish if the server on which the server is running, is of the specified type.
    Any non-False suffices, but extra information (like the server type and version) can be returned.
    E.g. when on a plesk-server the code `providers.plesk.is_server_type() is called, it returns a string with
    the version info."""
    return hostname == 'zh-dev-omni-001'


def get_domains():
    """Get all domains from the local hosting server."""
    return [f"domain-{i:03}.com" for i in range(1, 1001)]


def get_domain_info(domain):
    """Get detailed information about the specified domain from the local hosting server.
    When additional or different info is needed, change this function."""
    import time
    time.sleep(0.01)
    return {'domain': domain, 'ip': ip_address, 'mac': mac_address, 'hostname': hostname, 'now': now()}
