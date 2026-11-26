---
title: Installation
---

# Installation

This page installs Server to Sitekick on a hosting server: you get the code, add a configuration file, run the script
once by hand, schedule it with cron and check that the data arrives.

## Requirements

- **Linux** with cron reading `/etc/cron.d`.
- **Python 3.6 or later**, available as `python3`. The script uses only the standard library; there is nothing to
  install with `pip`.
- **Root access.** `install` writes the cron file `/etc/cron.d/domains-to-sitekick` and must run as root. The
  `plesk` command-line tool also needs root, so run `test plesk` and `send` as root on a Plesk server; the cron job
  runs as root.
- **Outgoing HTTPS** from the server to the hosts of the push URL (`SITEKICK_PUSH_URL`, or the URL you configure) and
  of the debug URL (`SITEKICK_DEBUG_URL`). Both defaults are set in `sitekick/config.py`; the `debug` provider
  contacts the debug URL on every run (see [Diagnostic mode](index.md#diagnostic-mode)).
- **A host name that resolves to the public IP address of the server.** The script takes the IP address it sends
  from the host name of the server; when the host name resolves to a loopback address, that address is sent instead.

## Get the code

The entry script `domains-to-sitekick.py` alone is not enough: it imports the `sitekick/` package, and it finds the
providers in the `providers/` directory next to it. Install the repository as a whole, in a directory owned by root,
for example `/usr/local/src/server-to-sitekick`:

```bash
git clone https://github.com/yourapi/server-to-sitekick.git /usr/local/src/server-to-sitekick
```

Without `git`, copy at least these parts of the repository, keeping their layout:

```text
/usr/local/src/server-to-sitekick/
├── domains-to-sitekick.py
├── sitekick/
└── providers/
```

Every `.py` file in `providers/` (except `__init__.py`) is loaded as a provider, so keep other Python files, such as
backup copies, out of that directory.

To update, pull the repository again (`git -C /usr/local/src/server-to-sitekick pull`) or copy the new files over the
old ones.

## Configuration file

Settings that differ from the defaults go into an optional configuration file, by default
`/etc/server-to-sitekick/config.py`. It is a Python file: the script executes it at start-up and reads the names
listed in [Commands and configuration](usage.md#configuration-file). Names that you leave out keep their default.

```python
# /etc/server-to-sitekick/config.py
QUEUE_PATH = '/var/spool/server-to-sitekick'
SITEKICK_PUSH_URL = 'https://api.example.com/sitekick/public/post/servers'
SYSTEM_INFO = True
GDPR_COMPLIANT = True
GDPR_PSK = 'replace-with-your-own-long-random-value'
```

- **Queue location.** The queue holds the records until they are sent. The default, `/tmp/sitekick/domains`, is
  under `/tmp`; set `QUEUE_PATH` to a directory outside `/tmp`, for example `/var/spool/server-to-sitekick`. The
  script creates the directory when it does not exist. A run pushes every file it finds in the queue, so give test
  runs a queue of their own with `--queue-path` (see [Testing](testing.md#safe-practice)).
- **Push URL.** Set `SITEKICK_PUSH_URL` when the Sitekick operator gives you a push URL. The Sitekick operator is the
  party that runs the Sitekick service you send to (see [Terms](index.md#terms)).

Because the file is executed as root and may hold the pre-shared key, create it as root and make the directory and
the file accessible to root only:

```bash
mkdir -p /etc/server-to-sitekick
chmod 700 /etc/server-to-sitekick
# write /etc/server-to-sitekick/config.py, then:
chmod 600 /etc/server-to-sitekick/config.py
```

A random key can be generated with `python3 -c "import secrets; print(secrets.token_hex(32))"`. See
[Privacy](data.md#privacy) for what the key is used for.

## First run

Run the commands as root, from any directory. First look at what the providers produce:

```bash
python3 /usr/local/src/server-to-sitekick/domains-to-sitekick.py test plesk
python3 /usr/local/src/server-to-sitekick/domains-to-sitekick.py test server
```

`test` prints the records for up to five domains and does not push records; see
[Commands and configuration](usage.md#test).

!!! warning "Decide on pseudonymisation before the first send"
    The script pseudonymises the owner contact name and the administrator email only when `GDPR_COMPLIANT` is
    true, at the moment a record is collected; records that were sent earlier stay as they were sent. Decide before
    the first `send` whether to set `GDPR_COMPLIANT = True`, and set your own `GDPR_PSK`: another key gives other
    pseudonyms for the same values. See [Privacy](data.md#privacy).

Then collect and send the data once:

```bash
python3 /usr/local/src/server-to-sitekick/domains-to-sitekick.py send
```

The script prints its progress and, for each batch, the number of records pushed; see
[Verify that data arrives](#verify-that-data-arrives).

## Schedule the daily run

```bash
python3 /usr/local/src/server-to-sitekick/domains-to-sitekick.py install
```

`install` (or `install daily`) writes `/etc/cron.d/domains-to-sitekick` with a daily run at a minute between 03:00
and 04:00, server time:

```text
# Run the domains-to-sitekick script daily at a random minute between 3 and 4 AM.
17 3 * * * root python3 /usr/local/src/server-to-sitekick/domains-to-sitekick.py
```

- The minute (17 in the example) is derived from the host name and IP address of the server, so it stays the same on
  every install on that server and differs between servers; a hosting platform does not push all at once.
- The line runs the script without a command, which means `send`.
- The line contains the full path of the script. If you move the code, run `install` again.
- Options that you pass to `install` are not copied into the cron line. Settings that the daily run needs belong in
  the [configuration file](#configuration-file).

### Diagnostic mode

The `debug` provider runs with every `send`, also in the daily run: it retrieves the diagnostic commands that the
Sitekick operator lists for this server, runs them with the privileges of the script (root under cron) and sends
their output (see [Diagnostic mode](index.md#diagnostic-mode)). On request of the Sitekick operator you can also
schedule the `debug` command, which runs this provider alone, every 5 minutes:

```bash
python3 /usr/local/src/server-to-sitekick/domains-to-sitekick.py install debug
```

This writes the same cron file with a run of the `debug` command every 5 minutes:

```text
# Debug the domains-to-sitekick script every 5 minutes.
*/5 * * * * root python3 /usr/local/src/server-to-sitekick/domains-to-sitekick.py debug
```

Because both modes use the same file, `install debug` replaces the daily schedule. To stop the 5-minute runs, run
`install` again: it rewrites the cron file to the daily line. See also
[Commands and configuration](usage.md#debug).

## Verify that data arrives

Run `send` by hand once and read its output. Each line starts with a timestamp, such as
`2026-11-26T03:17:05.123456+01:00`:

| Line | Meaning |
|---|---|
| `<n> <timestamp>: <domain> (Sitekick)`, then dots | Progress of the collection: a line for the first key and for every hundredth, a dot for each other key |
| `<timestamp> Sitekick info on <N> domains stored in <queue path>` | The collection of a provider has finished; `<N>` is the number of keys the provider listed |
| `<timestamp> Sitekick pushed another <k> of <total> files so far to <url>` | A batch was accepted |
| `<timestamp> Sitekick push attempt <a> of 10 to <url> failed with code <status>: <body>` | The push URL answered with a status other than 2xx; the batch is tried again |
| `<timestamp> Sitekick push attempt <a> of 10 to <url> failed with exception: <error>` | The push URL could not be reached; the batch is tried again |
| `<timestamp> Sitekick pushed total <N> files to <url>` | The push of a provider has finished; one such line per provider |

After a successful push the queue directory is empty:

```bash
ls -A /var/spool/server-to-sitekick
```

Files that remain were not delivered and go with the next run.

The cron job does not redirect its output. Cron mails the output of the job to root when the server has a mail
transport, and otherwise discards or logs it, depending on the cron daemon. The system log (for example
`journalctl -u cron`, `/var/log/syslog` or `/var/log/cron`) shows when the job ran. The Sitekick operator can confirm
that the records arrived.

## Uninstall

1. Remove the cron file: `rm /etc/cron.d/domains-to-sitekick`.
2. Remove the code: `rm -r /usr/local/src/server-to-sitekick`.
3. Remove the configuration directory, if you created it: `rm -r /etc/server-to-sitekick`.
4. Remove the queue directories: the directory you set as `QUEUE_PATH` (default `/tmp/sitekick/domains`) and any
   queue you used for tests, such as `/tmp/sitekick/test-queue`. They may still hold records that were not
   delivered.
5. Ask the Sitekick operator to delete the data that was already sent.
