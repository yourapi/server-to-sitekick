"""Plesk provider module for Sitekick. This module is used to get information from a Plesk server and send it to the
Sitekick server.
Plesk has two main information sources: the API and the CLI. The API is easy to use and returns data in json format,
but does not contain all information. The CLI is also callable through the API, but returns data in text format.
The cli is used to retrieve a complete list of domains and to get detailed information about a domain.
The text information is converted to json format, so it can be sent easily.
"""
import re

from sitekick import config
from sitekick.utils import hostname, ip_address, mac_address, cli, obfuscate

tokens = dict()

DOMAIN_COUNT_PER_POST = 10  # number of detailed domain info packages to send per post
DOMAIN_POST_INTERVAL = 5  # seconds


def is_server_type():
    """Get the server information from the command line. If the api is not available, it raises an exception so this provider
    is not used."""
    result = cli(['plesk', 'version'])
    return re.search(r'version.*\d+\.\d+', result, re.I + re.DOTALL)


def convert_domain_text_to_json(domain_info_lines: list) -> dict:
    """Get the domain info as a number of lines and convert it to Python dict structure. An example of the text output:
General
=============================
Domain name:                            sitekick.eu
Creation date:                          Oct 20, 2024

Hosting
=============================
Hosting type:                           Physical hosting
IP Address:                             145.131.8.226
FTP Login:                              sitekick.eu_34gqrbu1k9m

Web Users
=============================
Total :                                 0
PHP support:                            0


Must be converted to JSON:
{
    "General": {
        "Domain name": "sitekick.eu",
        "Creation date": "Oct 20, 2023",
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
    domain_info_text = cli(['plesk', 'bin', 'domain', '--info', domain])
    if config.GDPR_COMPLIANT:
        def obfuscate_contact_name(match):
            value = match.group(2)
            if not value:
                return match.group(1)
            return match.group(1) + obfuscate(value, config.GDPR_PSK)

        def obfuscate_admin_email(match):
            value = match.group(2)
            if not value:
                return match.group(1)
            return match.group(1) + obfuscate(value, config.GDPR_PSK)

        domain_info_output = re.sub(
            r"(Owner's contact name\s*:\s*)(.+)",
            obfuscate_contact_name,
            domain_info_text,
            flags=re.IGNORECASE,
        )
        domain_info_output = re.sub(
            r"(Administrator's email\s*:?\s*)(.+)",
            obfuscate_admin_email,
            domain_info_output,
            flags=re.IGNORECASE,
        )
    else:
        domain_info_output = domain_info_text
    result = {
        'Server': {'Hostname': hostname, 'IP-address': ip_address, 'MAC-address': mac_address},
        'provider': 'plesk',
        'domain': domain,
        'info': domain_info_output
    }
    # Convert the text info to a valid JSON string:
    domain_info = convert_domain_text_to_json(domain_info_text.split('\n'))
    domain_id = domain_info.get('General', {}).get('Domain ID')
    absolute_path = domain_info.get('Logrotation info', {}).get('--WWW-Root--')
    path = absolute_path.split(domain)[-1] if absolute_path else None
    if domain_id and path:
        domain_wp_plugin_info = cli(
            ['plesk', 'ext', 'wp-toolkit', '--info', '-main-domain-id', domain_id, '-path', path, '-format', 'raw'])
        if config.GDPR_COMPLIANT:
            domain_wp_plugin_info = re.sub(
                r"(Owner's contact name\s*:\s*)(.+)",
                obfuscate_contact_name,
                domain_wp_plugin_info,
                flags=re.IGNORECASE,
            )
            domain_wp_plugin_info = re.sub(
                r"(Administrator's email\s*:?\s*)(.+)",
                obfuscate_admin_email,
                domain_wp_plugin_info,
                flags=re.IGNORECASE,
            )
        result['wp_plugins'] = domain_wp_plugin_info
    return result
