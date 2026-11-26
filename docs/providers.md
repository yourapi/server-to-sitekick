---
title: Writing a provider
---

# Writing a provider

A provider teaches the script about one kind of server. The repository contains a provider for Plesk; the mechanism
is designed for other control panels as well, such as cPanel and DirectAdmin, and for custom hosting platforms. A
provider is a Python module in the `providers/` directory with three functions and the constants
`DOMAIN_COUNT_PER_POST` and `DOMAIN_POST_INTERVAL`, as in the template.

## How the script loads providers

On every run the script imports each `.py` file in `providers/`, except `__init__.py`, as `providers.<name>`. A
module is used when:

1. it imports without an error;
2. it has the attributes `is_server_type`, `get_domains` and `get_domain_info`;
3. `is_server_type()` returns a true value without raising an exception.

A module that does not import, lacks one of the functions or raises an exception in `is_server_type()` is skipped
with a message; a module whose `is_server_type()` returns a false value is skipped silently. The other providers run
as usual. The module name becomes `meta.type` in every record the provider sends, so choose a short, lower-case name
with underscores, such as `directadmin`.

## The three functions

### `is_server_type()`

Returns a true value when the provider applies to this server, and a false value or an exception when it does not.
Any true value works; the Plesk provider returns the match of the version in the output of `plesk version`. Keep it
fast and free of side effects: it runs on every run, for every provider, and also with `test`.

### `get_domains()`

Returns a list of strings, the keys of the records: for a control panel, the names of the domains on the server. The
script trims and lower-cases each name and skips names it has already seen. The key does not have to be a domain
name: the `server` provider returns the IP address of the server, so that it sends one record per run.

### `get_domain_info(domain)`

Receives one key from `get_domains()`, trimmed and in lower case, and returns a dictionary with the information about
it. The dictionary must be serialisable to JSON: strings, numbers, booleans, `None`, lists and dictionaries. Include
the domain name yourself if the receiving side needs it in the record, as the Plesk provider does under `domain`; the
script adds the key as `meta.domain`. Do not use the key `meta`: the script sets it (see
[The meta block](data.md#the-meta-block)).

When the function raises an exception, the script tries again and, after the last attempt, skips the domain for
this run; see [Data sent to Sitekick](data.md#the-request) for the retries.

## Constants

| Constant | Used for | Default for `None` |
|---|---|---|
| `DOMAIN_COUNT_PER_POST` | Maximum number of records per POST | 20 |
| `DOMAIN_POST_INTERVAL` | Designed for the pause between two POSTs, in seconds; the push step sends the next batch as soon as the previous one has been accepted | 10 |
| `EXECUTE_PARALLEL` | Optional. Designed for collecting and pushing at the same time, in two threads | |

- Define `DOMAIN_COUNT_PER_POST` and `DOMAIN_POST_INTERVAL` in every provider, as the template does: the `send`
  command reads both from the module and needs them to be present. A value of `None` selects the default.
- `send` and `debug` run collection and push one after the other, for every provider, whatever the value of
  `EXECUTE_PARALLEL`.

## Helpers

`sitekick.utils` offers helpers that the existing providers use:

| Helper | What it gives |
|---|---|
| `cli(command, include_stderr=True)` | Runs a command, given as a list of program and arguments (no shell), as the user that runs the script, and returns its output as one string: standard output followed by standard error, or only standard output with `include_stderr=False`. It does not raise on a non-zero exit status; when the program cannot be started, it returns a text that starts with the command and `failed:`. |
| `now()` | The current local time in ISO 8601, with the UTC offset |
| `hostname` | The host name of the server (a value, not a function) |
| `ip_address` | The IP address that the host name resolves to (a value) |
| `mac_address` | The MAC address, as six upper-case hexadecimal pairs separated by colons, or `None` (a value) |
| `obfuscate(value, psk, *, length=16)` | The HMAC-SHA256 pseudonym of `value` with the key `psk`, as `2 * length` hexadecimal characters; `None` stays `None` |

Because `cli()` does not raise on failure, check its output in `is_server_type()`, as the Plesk provider does with a
regular expression. The settings are available through `from sitekick import config`: read `config.GDPR_COMPLIANT`,
`config.GDPR_PSK` and `config.SYSTEM_INFO` inside your functions, and pseudonymise personal data with `obfuscate()`
when `config.GDPR_COMPLIANT` is true (see [Privacy](data.md#privacy)).

## Example: hello_world

Copy the template and give the copy the name of your provider:

```bash
cp providers/template.py providers/hello_world.py
```

Then replace the three functions. This example reports two fixed domains, and applies only on a server where the
file `/etc/hello-world-hosting` exists:

```python
"""Hello world provider: an example that reports two fixed domains."""
from pathlib import Path

from sitekick.utils import now, hostname, ip_address, mac_address

EXECUTE_PARALLEL = False
DOMAIN_COUNT_PER_POST = 10
DOMAIN_POST_INTERVAL = 1


def is_server_type():
    """True on a server with the hello-world marker file."""
    return Path('/etc/hello-world-hosting').exists()


def get_domains():
    """All domains on this server."""
    return ['example.com', 'example.org']


def get_domain_info(domain):
    """The information about one domain."""
    return {'domain': domain, 'hostname': hostname, 'ip': ip_address, 'mac': mac_address, 'now': now()}
```

A real provider calls the control panel instead, for example with `cli(['/usr/local/bin/panel', 'list-domains'])`,
and parses its output.

## Test it

```bash
python3 domains-to-sitekick.py test hello_world
```

`test` runs the provider even where `is_server_type()` is false, and prints what it returns (see
[Commands and configuration](usage.md#test)):

```text
=== Testing module providers.hello_world ===
providers.hello_world.is_server_type(): False
Found 2 domains in providers.hello_world.get_domains()
Sample of domains: example.com, example.org
Testing 'example.com'...
--------------------------------------------------------------------------------
{   'domain': 'example.com',
    'hostname': 'web01.example.com',
    'ip': '192.0.2.10',
    'mac': '00:00:5E:00:53:01',
    'now': '2026-11-26T10:15:00.123456+01:00'}
Testing 'example.org'...
--------------------------------------------------------------------------------
{   'domain': 'example.org',
    ...
```

During development `python3 domains-to-sitekick.py test` is enough: without an argument it tests the provider file
you changed last. To see the records arrive as the platform would receive them, send them to a local echo server;
see [Testing](testing.md#a-local-echo-server).

## The receiving side

Every record carries the provider name in `meta.type`. The Sitekick push endpoint accepts the records of any
provider, but the platform does something useful with them only when a connector processes that kind of data: for
Plesk, the [`plesk` domain connector](https://yourapi.github.io/sitekick-connectors/catalogue/hosting-domain/#plesk)
in the sitekick-connectors repository. A new provider therefore comes with a matching connector, and possibly a
platform function that parses its output. Agree on the provider name and the record layout with the Sitekick
operator, and see the [Sitekick connectors site](https://yourapi.github.io/sitekick-connectors/) for how to write and
propose a connector.

Propose the provider itself through a pull request on
[server-to-sitekick](https://github.com/yourapi/server-to-sitekick), with a sample of its output made with `test`
and example values only.
