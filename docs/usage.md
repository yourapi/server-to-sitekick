---
title: Commands and configuration
---

# Commands and configuration

```text
python3 domains-to-sitekick.py [options] [command] [arguments]
```

Without a command the script runs `send`. Put the options before the command. `-h` or `--help` lists the commands
and options; `--version` prints the version (`domains-to-sitekick 0.2`).

## Commands

| Command | What it does |
|---|---|
| `send` | Collects the data of every provider that applies to this server and pushes it to Sitekick. The default command. |
| `install`, `install daily`, `install debug` | Writes the cron file `/etc/cron.d/domains-to-sitekick`. `daily` (the default) runs `send` once a day; `debug` runs `debug` every 5 minutes. Must run as root. |
| `test`, `test <argument>` | Shows what providers produce; it does not queue or push records. Testing the `debug` provider retrieves and runs its commands. The argument is a provider name, `latest`, `all` or a comma-separated list of names. |
| `debug` | Runs the `debug` provider alone: retrieves the diagnostic commands for this server, runs them and sends their output. |

### `send`

For each provider whose `is_server_type()` is true, `send` lists the domains, collects their information into the
queue directory and then pushes the queue to the push URL in batches; collection and push run one after the other.
The `debug` provider applies to every server, so `send` also runs the diagnostic commands (see [`debug`](#debug)).
The batch sizes and retries are described in [Data sent to Sitekick](data.md#the-request).

### `install`

`install` and `install daily` schedule a daily run at a fixed minute between 03:00 and 04:00; `install debug`
schedules the diagnostic mode every 5 minutes. Both write the same file, so the last `install` wins. The cron lines
are shown in [Installation](installation.md#schedule-the-daily-run). The cron line does not carry options: put
settings for scheduled runs in the [configuration file](#configuration-file).

### `test`

| Argument | Providers tested |
|---|---|
| none, or `latest` | The provider whose file in `providers/` was changed most recently |
| `all` | Every provider in `providers/` |
| a name, such as `plesk` | That provider |
| names separated by commas, such as `plesk,server` | Those providers |

For each provider, `test` prints the result of `is_server_type()`, the number of domains from `get_domains()` with a
sample of up to five, and the record that `get_domain_info()` returns for each domain in the sample. It tests a
provider even when `is_server_type()` is false, so you can develop a provider on another machine. The records are
printed as the provider returns them, without the `meta` block. `test` does not queue or push records.

`all` includes the `debug` provider: testing it retrieves the diagnostic commands for this server from the Sitekick
service and runs up to five of them, with the privileges of the user that runs `test`; their output is printed, not
pushed. `all` also includes the development providers `template` and `test_body`.

Run `test plesk` as root on a Plesk server, because the `plesk` tool needs root. Look at the output before the first
`send`: it is the data that will be sent (see [Data sent to Sitekick](data.md)). To see the records with their
`meta` blocks as the platform receives them, use the echo server described in
[Testing](testing.md#a-local-echo-server).

### `debug`

The `debug` provider applies to every server, so every `send`, including the daily cron run, runs it together with
the other providers. The `debug` command runs this provider alone; on request of the Sitekick operator it is
scheduled every 5 minutes with `install debug`, and running `install` again rewrites the cron file to the daily line.
The Sitekick operator defines the diagnostic commands. A run of the provider:

1. retrieves the list of diagnostic commands from the Sitekick debug endpoint (`SITEKICK_DEBUG_URL` in
   `sitekick/config.py`), passing the host name of the server;
2. selects the commands whose pattern matches the host name, IP address or MAC address of the server (a
   case-insensitive regular expression that must match the whole value);
3. runs each command with the privileges of the user that runs the script (root under cron), and keeps its output
   (standard output and standard error);
4. sends one record per command, with the output, to the push URL, in batches of 10.

## Options

| Option | Default | Meaning |
|---|---|---|
| `--config-path PATH` | `/etc/server-to-sitekick` | Configuration directory that holds `config.py`, or the path of a configuration file itself |
| `--queue-path PATH` | `/tmp/sitekick/domains` | Queue directory; created when it does not exist. See [Installation](installation.md#configuration-file) for the recommended location |
| `--sitekick-url URL` | The Sitekick push endpoint (`SITEKICK_PUSH_URL` in `sitekick/config.py`) | URL to which the records are posted |
| `--system-info`, `--no-system-info` | Off | Add the output of `uptime`, `free`, `df` and `lscpu` to the `server` record |
| `--gdpr-compliant`, `--no-gdpr-compliant` | Off | Pseudonymise the owner contact name and the administrator email in the Plesk output, see [Privacy](data.md#privacy) |
| `--gdpr-psk KEY` | A placeholder value in `sitekick/config.py` | Pre-shared key for the pseudonyms; set your own and keep it secret |
| `--enable-autoupdate` | Off | Designed for automatic updates of the code from the public repository |
| `--version` | | Print the version and stop |
| `-h`, `--help` | | Print the help and stop |

Pass the pre-shared key in the configuration file rather than with `--gdpr-psk`: a value on the command line is
visible in the process list and in the shell history.

## Configuration file

At start-up the script looks for a configuration file before it reads the other options:

- `--config-path` names a directory: the script reads `config.py` in that directory.
- `--config-path` names a file: the script reads that file.
- Without `--config-path`: the script reads `/etc/server-to-sitekick/config.py`.
- When the file does not exist, the script runs with the defaults.

The file is Python. The script executes it and takes these names from it; other names are ignored:

| Name | Type | Same as |
|---|---|---|
| `QUEUE_PATH` | str | `--queue-path` |
| `SITEKICK_PUSH_URL` | str | `--sitekick-url` |
| `SYSTEM_INFO` | bool | `--system-info` / `--no-system-info` |
| `GDPR_COMPLIANT` | bool | `--gdpr-compliant` / `--no-gdpr-compliant` |
| `GDPR_PSK` | str | `--gdpr-psk` |
| `ENABLE_AUTOUPDATE` | bool | `--enable-autoupdate` |

**Precedence.** The built-in defaults in `sitekick/config.py` come first. Values in the configuration file replace
them and become the defaults of the options. An option given on the command line replaces both.

An example file is shown in [Installation](installation.md#configuration-file).

## Location of the plesk binary

The `plesk` provider first looks up the `plesk` command with `which plesk`. When that finds nothing, for example
under cron, whose search path is short, it uses `PLESK_BINARY`, by default `/usr/sbin/plesk`. `PLESK_BINARY` is a
setting in `sitekick/config.py` only; it is not read from the configuration file.

## Examples

```bash
# Send with the defaults (the same as running without a command)
python3 domains-to-sitekick.py send

# Send to another push URL, with another queue directory
python3 domains-to-sitekick.py --queue-path /var/spool/server-to-sitekick \
    --sitekick-url https://api.example.com/sitekick/public/post/servers send

# Use a configuration directory or a configuration file
python3 domains-to-sitekick.py --config-path /opt/sitekick-config send
python3 domains-to-sitekick.py --config-path /opt/sitekick-config/config.py send

# Send with system information and pseudonymised personal data (GDPR_PSK set in the configuration file)
python3 domains-to-sitekick.py --system-info --gdpr-compliant send

# Override a configuration-file setting for one run
python3 domains-to-sitekick.py --no-system-info send

# Test the Plesk provider, then all providers
python3 domains-to-sitekick.py test plesk
python3 domains-to-sitekick.py test all

# Schedule the daily run, or the diagnostic mode
python3 domains-to-sitekick.py install
python3 domains-to-sitekick.py install debug
```
