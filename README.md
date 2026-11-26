# Server to Sitekick

**Documentation:** <https://yourapi.github.io/server-to-sitekick/>

Server to Sitekick runs on a hosting server, collects data about the domains it hosts and about the server itself,
and sends that data to the Sitekick hosting intelligence platform. Sitekick combines it with the public data it
collects about the domains it monitors. The repository contains a provider for Plesk and one for general Linux server
data; the provider mechanism is designed for other control panels as well, such as cPanel and DirectAdmin.

The script needs Python 3.6 or later and uses only the standard library.

## Quick start

As root, on the hosting server:

```bash
# Get the code (the script needs the sitekick/ and providers/ directories next to it)
git clone https://github.com/yourapi/server-to-sitekick.git /usr/local/src/server-to-sitekick
cd /usr/local/src/server-to-sitekick

# Configuration file: settings for every run, including the scheduled runs
mkdir -p /etc/server-to-sitekick && chmod 700 /etc/server-to-sitekick
# write /etc/server-to-sitekick/config.py (QUEUE_PATH, SITEKICK_PUSH_URL, GDPR_COMPLIANT, GDPR_PSK), then:
chmod 600 /etc/server-to-sitekick/config.py

# See what the Plesk provider produces; test does not push records
python3 domains-to-sitekick.py test plesk
```

> **Before the first `send`:** decide on pseudonymisation. Set `GDPR_COMPLIANT = True` and your own `GDPR_PSK` in the
> configuration file if the owner contact name and the administrator email must be pseudonymised; records already
> sent stay as they were sent. See
> [Privacy](https://yourapi.github.io/server-to-sitekick/data/#privacy).

```bash
# Collect and send the data once
python3 domains-to-sitekick.py send

# Schedule a daily run between 03:00 and 04:00 (writes /etc/cron.d/domains-to-sitekick)
python3 domains-to-sitekick.py install
```

The configuration file and the first run are described in
[Installation](https://yourapi.github.io/server-to-sitekick/installation/).

## Commands and options

The commands are `send` (the default), `install` and `test [provider|latest|all]`. The options used most:

- `--queue-path PATH`: the queue directory (default `/tmp/sitekick/domains`).
- `--sitekick-url URL`: the URL to which the records are posted (default: the Sitekick push endpoint,
  `SITEKICK_PUSH_URL` in `sitekick/config.py`).
- `--system-info`, `--no-system-info`: add the output of `uptime`, `free`, `df` and `lscpu` to the server record
  (default off).
- `--gdpr-compliant`, `--no-gdpr-compliant`: pseudonymise the owner contact name and the administrator email in the
  Plesk output (default off).

Every command and option is described in
[Commands and configuration](https://yourapi.github.io/server-to-sitekick/usage/).

## Documentation

- [Overview](https://yourapi.github.io/server-to-sitekick/): what the script does and how it works
- [Installation](https://yourapi.github.io/server-to-sitekick/installation/): requirements, configuration file, first
  run, cron job, checking that data arrives, uninstalling
- [Commands and configuration](https://yourapi.github.io/server-to-sitekick/usage/): every command and option
- [Data sent to Sitekick](https://yourapi.github.io/server-to-sitekick/data/): the request, the records and privacy
- [Writing a provider](https://yourapi.github.io/server-to-sitekick/providers/): support for another kind of server
- [Testing](https://yourapi.github.io/server-to-sitekick/testing/): unit tests and an echo server

## Adding a provider

A provider is a module in `providers/` with three functions, `is_server_type()`, `get_domains()` and
`get_domain_info(domain)`, and the constants `DOMAIN_COUNT_PER_POST` and `DOMAIN_POST_INTERVAL`, as in the template.
Copy `providers/template.py`, implement the functions for your platform and check the result with
`python3 domains-to-sitekick.py test <name>`. The records reach Sitekick with the module name in `meta.type`; a new
provider needs a matching connector in [sitekick-connectors](https://yourapi.github.io/sitekick-connectors/). See
[Writing a provider](https://yourapi.github.io/server-to-sitekick/providers/).

## Testing

```bash
pytest -q                                    # unit tests, on a development machine
python3 domains-to-sitekick.py test all      # what every provider produces
python3 test_server.py                       # echo server on port 8000; only on a test machine
python3 domains-to-sitekick.py --queue-path /tmp/sitekick/test-queue \
    --sitekick-url http://127.0.0.1:8000/ send
```

See [Testing](https://yourapi.github.io/server-to-sitekick/testing/).

## Licence

Apache License 2.0; see [LICENSE](LICENSE).
