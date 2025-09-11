"""Plesk provider module for Sitekick. This module is used to get information from a Plesk server and send it to the
Sitekick server.
Plesk has two main information sources: the API and the CLI. The API is easy to use and returns data in json format,
but does not contain all information. The CLI is also callable through the API, but returns data in text format.
The cli is used to retrieve a complete list of domains and to get detailed information about a domain.
The text information is converted to json format, so it can be sent easily.
"""
import json
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

from sitekick.utils import now, hostname, ip_address, mac_address

tokens = dict()

DOMAIN_COUNT_PER_POST = 200  # number of detailed domain info packages to send per post
DOMAIN_POST_INTERVAL = 100  # seconds


def is_server_type():
    """Get the server information from the api. If the api is not available, it raises an exception so this provider
    is not used."""
    return get_info_api('server')


def get_token(filename=f'/etc/plesk/tokens.json'):
    """Get a token for local API access. If it was not generated, generate a new one and store it in a safe location."""
    global tokens
    if hostname in tokens:
        return tokens[hostname]
    try:
        with open(filename) as f:
            tokens = json.loads(f.read())
            return tokens[hostname]
    except:
        # No token stored for this server. Generate a new one and store it in a safe location.
        # Get a token with the plesk bin secret_key tool and store it. First get the local IP-address:
        proc = subprocess.run(["plesk", "bin", "secret_key", "-c", "-ip-address", ip_address, "-description",
                               f"Admin access token for {hostname} at {now()}"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Now the token is in the output of the command. Store it in a safe location:
        token = proc.stdout.decode().strip()
        try:
            with Path(filename).open() as f:
                tokens = json.loads(f.read())
        except:
            tokens = {}
        tokens[hostname] = token
        # Create paths if necessary:
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            f.write(json.dumps(tokens))
        return token


def get_info_api(endpoint, method=None, data=None):
    """Get the specified information form the specified end point on the local Plesk server. For information on getting
    Plesk information: https://docs.plesk.com/en-US/obsidian/api-rpc/about-rest-api.79359/"""
    url = f"https://{hostname}:8443/api/v2/{endpoint}"
    req = Request(url,
                  data=data,
                  headers={
                      'X-API-Key': get_token(),
                      'Content-Type': 'application/json',
                      'Accept': 'application/json'},
                  method=method)
    response = urlopen(req)
    result = response.read()
    try:
        return json.loads(result)
    except:
        try:
            return result.decode()
        except:
            return result


def get_info_cli(command):
    """Get the specified information form the specified end point on the local Plesk server using the CLI. The CLI is
     executed using the API"""
    # In Python 3.6, you use stdout=PIPE to capture the output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # The output is in bytes, so you must decode it to a string
    output_string = result.stdout.decode('utf-8')
    lines = output_string.split('\n')
    if lines and '\t' in lines[0]:
        return [dict([line.split('\t', 1)]) for line in lines]
    return lines

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
    return [line.strip() for line in get_info_cli('plesk bin site --list'.split()) if line.strip()]


def get_domain_info(domain):
    """Get detailed information about the specified domain from the local Plesk server.
    When additional or different info is needed, change this function."""
    domain_info_lines = get_info_cli('plesk bin domain --info'.split() + [domain])
    # Convert the text info to a valid JSON string:
    domain_info = convert_domain_text_to_json(domain_info_lines)
    domain_id = domain_info.get('General', {}).get('Domain ID')
    absolute_path = domain_info.get('Logrotation info', {}).get('--WWW-Root--')
    path = absolute_path.split(domain)[-1] if absolute_path else None
    print('=' * 100)
    print(domain_id, path)
    print('=' * 100)
    if domain_id and path:
        domain_wp_plugin_lines = get_info_cli(['plesk', 'ext', 'wp-toolkit', '--info', '-main-domain-id', domain_id, '-path', path, '-format', 'raw'])
        domain_info['wp_plugins'] = convert_domain_text_to_json(domain_wp_plugin_lines)
    domain_info['Server'] = {'Hostname': hostname, 'IP-address': ip_address, 'MAC-address': mac_address}
    domain_info['domain'] = domain
    return domain_info
