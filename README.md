# Server To Sitekick
Connect a hosting server to the Sitekick domain analysis and monitoring services. The hosting server can be any of a
number of systems, like: Plesk, cPanel, DirectAdmin, etc. Any provider can be added easily by adding a new module with 
a small number of implemented Python-functions.

## Introduction
Sitekick is a domain analysis and monitoring service that provides a comprehensive overview of the health of your domains.
Sitekick is used by major hosters for a number of applications: analysis, marketing, retention, monitoring, and more.
A major source of data is the actual hosting data, as it is provisioned by the hoster. 
This repository provides a simple way to connect any hosting server to Sitekick in a secure way.
A major source of data is the actual hosting data, as it is provisioned by the hoster.

This repository provides a simple way to connect a Plesk server to Sitekick in a secure way but can be easily extended 
to other providers, like cPanel, directadmin or custom hosting solutions.

## Installation
The file is a Python (3.5+) compatible script. It can be run on any Plesk server that has Python installed. The script
can be executed by calling python3, followed by the script name. The script has no dependencies on external modules. 
1. Copy the file `domains-to-sitekick.py` to a location of your choice, e.g. `/usr/local/bin/` or
`/usr/local/src/`.
2. To run the script, run: `python3 /usr/local/src/domains-to-sitekick.py`

The script loads a number of files dynamically. These files and paths will be created in the same directory as the 
script, so the current user should have write rights on the install directory. 

## Usage
The script can be used with optional command line arguments and options. The following commands are available:

### Commands
`python3 domains-to-sitekick.py send` or `python3 domains-to-sitekick.py`:
- `send`: Send the data to Sitekick. This is the default action. All domains are retrieved and sent to Sitekick.
- `install`: Install the script as a cronjob. The script will run every day between 3 and 4 AM, on a random minute which
is determined by the hostname, so it is repeatable.
- `test [provider]`: Test the specified provider and print sample domain info objects (the same kind of data that would
eventually be queued and POSTed to the API during `send`). If omitted or `latest`, the last changed provider is tested.
If `all`, all providers are tested. If it is the name of a provider (e.g. `plesk` or `template`), only that specific
provider is tested.

### Options
- `--version`: Show the version number and exit.
- `--config-path PATH`: Path to a configuration directory (containing `config.py`) or a direct path to a `config.py` file (default: `/etc/server-to-sitekick`). If present, values from this config are loaded before parsing options, so they become the CLI defaults. Explicit CLI options still take precedence.
- `--queue-path PATH`: Path to queue directory (default: `/tmp/sitekick/domains`). This option overrides the default queue directory.
- `--sitekick-url URL`: Sitekick push URL (default: `https://eu.sitekick.online/sitekick/public/post/servers`). This option overrides the default push URL.
- `--enable-autoupdate`: Enable automatic updates (default: disabled). When enabled, `load_code()` runs during startup before executing the command and refreshes local code from the upstream `server-to-sitekick` repository (via the Sitekick update endpoint).
- `--gdpr-compliant`, `--no-gdpr-compliant`: Enable or disable GDPR compliant behavior (default: disabled).
- `--gdpr-psk KEY`: Pre-shared key used for GDPR HMAC (default: configured value). Treat this as a secret.
- `--system-info`, `--no-system-info`: Enable or disable system info collection for the server provider (default: enabled).

### Examples
```bash
# Send domains using default settings
python3 domains-to-sitekick.py send

# Send domains with a custom configuration directory or file
python3 domains-to-sitekick.py --config-path /custom/config send
python3 domains-to-sitekick.py --config-path /custom/config/config.py send

# Test a provider with a custom queue path
python3 domains-to-sitekick.py --queue-path /var/queue test plesk

# Install as cron job with custom Sitekick URL
python3 domains-to-sitekick.py --sitekick-url https://custom.sitekick.url/api install

# Send domains with autoupdate enabled
python3 domains-to-sitekick.py --enable-autoupdate send

# Send domains without collecting system info
python3 domains-to-sitekick.py --no-system-info send

# Send domains with GDPR disabled and a custom PSK
python3 domains-to-sitekick.py --no-gdpr-compliant --gdpr-psk "my-psk" send
```

## Testing
Run unit tests:

```bash
pytest -q
```

Preview provider output (what will be sent to the API during `send`):

```bash
python3 domains-to-sitekick.py test plesk
```

Inspect incoming JSON posted to a local endpoint (useful while integrating the push call). Start the local echo server:

```bash
python3 test_server.py
```

Then point your Sitekick push URL at it, for example:

```bash
python3 domains-to-sitekick.py --sitekick-url http://127.0.0.1:8000/ send
```

## Adding new providers

### Provider modules
The script is designed to be easily extended with new providers. A provider is a module that contains three required 
functions. When placed in the right directory, the script will automatically load the module and execute the functions.

### Build a new provider
To build a new provider, copy the `template.py` file to a new file in the `providers` directory with an appropriate 
name. Making your first `hello_world` provider can be done in one step:
1. Copy the `template.py` file to `hello_world.py` in the `providers` directory.

To test this new provider, run the script with the `test` option: `python3 domains-to-sitekick.py test hello_world` or
just run `python3 domains-to-sitekick.py test`, which will just test the last changed file. The output should look like:
```=== Testing module providers.hello_world ===
providers.template.is_server_type(): False
Found 1000 domains in providers.template.get_domains()
Sample of domains: domain-446.com, domain-595.com, domain-736.com, domain-823.com, domain-934.com
Testing 'domain-446.com'...
--------------------------------------------------------------------------------
{   'domain': 'domain-446.com',
    'hostname': 'XPS17',
    'ip': '127.0.1.1',
    'mac': '00:15:5D:E5:05:B2',
    'now': '2023-11-06 09:42:00'}
...
--------------------------------------------------------------------------------
{   'domain': 'domain-934.com',
    'hostname': 'XPS17',
    'ip': '127.0.1.1',
    'mac': '00:15:5D:E5:05:B2',
    'now': '2023-11-06 09:42:01'}

Process finished with exit code 0

```
Now change the code of the 3 functions to suit this hosting server type. The functions are described below.

#### is_server_type()
Returns True if the current server is of the type that this provider supports. Can be any appropriate call, like
determining the presence of a file or calling the supposed provider API. If the API is not present, it may simply fail.

#### get_domains()
Returns a list of domains on this server. For every domain in this list, the specified domain info is retrieved.

#### get_domain_info(domain)
Return the specified domain info for this domain, like number of mailboxes, storage, bandwidth used etc. The function 
should return a dict with a `"domain": "<domain name>"` entry.