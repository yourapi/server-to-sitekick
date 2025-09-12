"""Plesk provider module for Sitekick. This module is used to get information from a Plesk server and send it to the
Sitekick server.
Plesk has two main information sources: the API and the CLI. The API is easy to use and returns data in json format,
but does not contain all information. The CLI is also callable through the API, but returns data in text format.
The cli is used to retrieve a complete list of domains and to get detailed information about a domain.
The text information is converted to json format, so it can be sent easily.
"""
from sitekick.utils import hostname, ip_address, mac_address, cli

tokens = dict()

DOMAIN_COUNT_PER_POST = 200  # number of detailed domain info packages to send per post
DOMAIN_POST_INTERVAL = 100  # seconds


def is_server_type():
    """Get the server information from the api. If the api is not available, it raises an exception so this provider
    is not used."""
    result = cli(['plesk', 'version'])
    return result if 'version' in result else None


def convert_domain_text_to_json(domain_info_lines: list) -> dict:
    """Get the domain info as a number of lines and convert it to Python dict structure. An example of the text output:
General
=============================
Domain name:                            sitekick.eu
Owner's contact name:                   Administrator (admin)
Domain status:                          OK
Creation date:                          Oct 20, 2023
Total size of backup files in local storage:0 B
Traffic:                                0 B/Month

Hosting
=============================
Hosting type:                           Physical hosting
IP Address:                             145.131.8.226
FTP Login:                              sitekick.eu_34gqrbu1k9m
FTP Password:                           ************
SSH access to the server shell under the subscription's system user:/bin/false
Hard disk quota:                        Unlimited (not supported)
Disk space used by httpdocs:            96.0 KB
Disk space used by Log files and statistical reports:28.0 KB
SSL/TLS support:                        On
Permanent SEO-safe 301 redirect from HTTP to HTTPS:On
PHP support:                            Yes
Python support:                         No
Web statistics:                         AWStats
Anonymous FTP:                          No
Disk space used by Anonymous FTP:       0 B

Web Users
=============================
Total :                                 0
PHP support:                            0
Python support:                         0
Total size:                             0 B

Mail Accounts
=============================
Mail service:                           On
Total :                                 3
Total size:                             0 B
Mail autodiscover:                      On

Must be converted to JSON:
{
    "General": {
        "Domain name": "sitekick.eu",
        "Owner\"s contact name": "Administrator (admin)",
        "Domain status": "OK",
        "Creation date": "Oct 20, 2023",
        "Total size of backup files in local storage": "0 B",
        "Traffic": "0 B/Month"
    },
    "Hosting": {
        "Hosting type": "Physical hosting",
        "IP Address": "..."
    }
}"""
    result = {}
    current_section = None
    prev_line = None
    for line in domain_info_lines:
        if line.startswith('==='):
            current_section = prev_line
            result[current_section] = {}
        elif current_section and line and ':' in line:
            key, value = line.split(':', 1)
            result[current_section][key.strip()] = value.strip()
        prev_line = line
    return result


def get_domains():
    """Get all domains from the local Plesk server."""
    return [line.strip() for line in cli(['plesk', 'bin', 'site', '--list']).split('\n') if line.strip()]


def get_domain_info(domain):
    """Get detailed information about the specified domain from the local Plesk server.
    When additional or different info is needed, change this function."""
    domain_info = cli(['plesk', 'bin', 'domain', '--info', domain])
    result = {
        'Server': {'Hostname': hostname, 'IP-address': ip_address, 'MAC-address': mac_address},
        'provider': 'plesk',
        'domain': domain,
        'info': domain_info
    }
    # Convert the text info to a valid JSON string:
    domain_info = convert_domain_text_to_json(domain_info.split('\n'))
    domain_id = domain_info.get('General', {}).get('Domain ID')
    absolute_path = domain_info.get('Logrotation info', {}).get('--WWW-Root--')
    path = absolute_path.split(domain)[-1] if absolute_path else None
    if domain_id and path:
        domain_wp_plugin_info = cli(
            ['plesk', 'ext', 'wp-toolkit', '--info', '-main-domain-id', domain_id, '-path', path, '-format', 'raw'])
        result['wp_plugins'] = domain_wp_plugin_info
    return result
