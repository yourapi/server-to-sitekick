---
title: Data sent to Sitekick
---

# Data sent to Sitekick

This page describes exactly what the script sends: the HTTP request, the `meta` block that every record carries, and
the records of the `plesk` and `server` providers. Use `test` to see the records of your own server before
you send them (see [Commands and configuration](usage.md#test)).

## The request

The script sends the records with HTTP POST requests to the push URL: by default the Sitekick push endpoint
(`SITEKICK_PUSH_URL` in `sitekick/config.py`), otherwise the URL from `--sitekick-url` or the configuration file, for
example `https://api.example.com/sitekick/public/post/servers`.

```text
POST /sitekick/public/post/servers HTTP/1.1
Host: api.example.com
Content-Type: application/json
Accept: application/json

{"data": [ {record}, {record}, ... ]}
```

The body is a JSON object with one key, `data`, whose value is a list of records. The records come from the queue
directory, one JSON file per record, named after its sequence number and key, such as `00000000-example.com.json`.
The files are sent in name order.

**Batches.** Each POST carries at most the provider's `DOMAIN_COUNT_PER_POST` records:

| Provider | Records per POST (`DOMAIN_COUNT_PER_POST`) | `DOMAIN_POST_INTERVAL` |
|---|---|---|
| `plesk` | 10 | 5 seconds |
| `server` | 10 | 1 second |
| `template` | 10 | 1 second |
| `test_body` | 20 | 1 second |

A provider that sets a constant to `None` gets the default: 20 records per POST and an interval of 10 seconds. The
interval is designed for spacing out the POSTs of a provider; the push step sends the next batch as soon as the
previous one has been accepted.

**Retries.** A response with a 2xx status code counts as accepted: the files of the batch are removed from the queue
and the next batch follows. Any other outcome, such as another status code or a connection error, is tried again, up
to 10 attempts per batch. The wait after a failed attempt grows exponentially from 1 second to 60 seconds (1, 1.6,
2.5, 3.9, 6.2, 9.7, 15, 24, 38 and 60 seconds). When all 10 attempts fail, the push stops; the files stay in the queue
and are sent with the next run.

**Collection retries.** Collecting the information of one domain is also tried up to 10 times, with waits that grow
from 1 to 5 seconds. A domain that still fails is skipped in this run. Domain names are trimmed and lower-cased, and a
domain that appears twice in the list is collected once.

## The meta block

The script adds a `meta` block to every record. A key `meta` that the provider returns itself is replaced.

| Field | Value |
|---|---|
| `type` | The name of the provider module, such as `plesk` or `server` |
| `domain` | The key of the record: the domain name for `plesk`, the IP address of the server for `server` |
| `hostname` | The host name of the server |
| `ip` | The IP address that the host name of the server resolves to |
| `timestamp` | The moment of collection, in ISO 8601 with the local UTC offset, such as `2026-11-26T03:17:05.123456+01:00` |
| `mac` | The MAC address of the server, as six upper-case hexadecimal pairs separated by colons |

The platform stores this server identity with each record; linking servers to the domains they host is designed
for. The IP address is the address that the host name resolves to (see
[Requirements](installation.md#requirements)).

## Plesk record

The `plesk` provider is designed for one record per domain on the server. The list of domains comes from
`plesk bin site --list`.

| Field | Content | Source |
|---|---|---|
| `Server` | `Hostname`, `IP-address` and `MAC-address` of the server | As in `meta` |
| `provider` | `plesk` | |
| `provider-version` | The version of the provider module, such as `260712` | |
| `plesk-version` | The text output of `plesk version` | `plesk version` |
| `php-version` | The domain name and its PHP handler, such as `plesk-php83-fpm`, tab-separated | `plesk db -sNe "SELECT d.name, h.php_handler_id FROM domains d JOIN hosting h ON h.dom_id=d.id WHERE d.name='<domain>'"` |
| `domain` | The domain name | |
| `info` | The text output of the domain information: sections such as General, Hosting, Web Users, Mail Accounts, Databases, Logrotation info and Subscription Information | `plesk bin domain --info <domain>` |
| `wp_plugins` | The text output of WP Toolkit for the website: the WordPress installation with its version and state, and its plugins and themes. Present only when the domain information contains a domain ID and a document root | `plesk ext wp-toolkit --info -main-domain-id <id> -path <path> -format raw` |

For `wp_plugins`, `<id>` is the `Domain ID` from the General section of the domain information, and `<path>` is the
part of the document root (`--WWW-Root--`) after the domain name, such as `/httpdocs`. When WP Toolkit manages no
WordPress site at that path, the field holds the message of WP Toolkit.

The text fields are sent as the Plesk tools print them, including messages on standard error; the receiving side
parses them.

## Server record

The `server` provider sends one record per run, keyed by the IP address of the server.

| Field | Content |
|---|---|
| `hostname`, `ip`, `mac` | The identity of the server, as in `meta` |
| `now` | The moment of collection, in the same format as `meta.timestamp` |
| `uptime`, `free`, `df`, `lscpu` | The text output of these commands; only with system information enabled (`--system-info` or `SYSTEM_INFO = True`, off by default) |

## Example

A shortened Plesk record, with example values:

```json
{
    "data": [
        {
            "Server": {
                "Hostname": "web01.example.com",
                "IP-address": "192.0.2.10",
                "MAC-address": "00:00:5E:00:53:01"
            },
            "provider": "plesk",
            "provider-version": "260712",
            "plesk-version": "Product version: Plesk Obsidian 18.0 ...",
            "php-version": "example.com\tplesk-php83-fpm\n",
            "domain": "example.com",
            "info": "General\n=============================\nDomain name:        example.com\n...",
            "wp_plugins": "...\nName                               Example site\nVersion                            6.8\n...",
            "meta": {
                "type": "plesk",
                "domain": "example.com",
                "hostname": "web01.example.com",
                "ip": "192.0.2.10",
                "timestamp": "2026-11-26T03:17:05.123456+01:00",
                "mac": "00:00:5E:00:53:01"
            }
        }
    ]
}
```

## Privacy

The Plesk output can contain personal data. The section names below are those of `plesk bin domain --info` and of the
WP Toolkit output.

| Data | Where | With `--gdpr-compliant` |
|---|---|---|
| Owner's contact name | `info`, section General | Pseudonymised |
| Administrator's email of the WordPress site | `wp_plugins` | Pseudonymised |
| FTP login of the domain | `info`, section Hosting | Sent as Plesk reports it |
| Owner of the subscription | `info`, section Subscription Information | Sent as Plesk reports it |
| Web users, mail accounts and databases | `info`, sections Web Users, Mail Accounts and Databases | Sent as Plesk reports them |

When your Plesk version lists mail account addresses or web and database user names in the sections Web Users, Mail
Accounts and Databases, those are sent as well. Run `test plesk` to see what your servers report.

### Pseudonymisation

With `--gdpr-compliant` (or `GDPR_COMPLIANT = True` in the configuration file) the script replaces the value on the
lines `Owner's contact name` and `Administrator's email`, in both `info` and `wp_plugins`, by a pseudonym before the
record is queued:

```text
Owner's contact name:                   4f0c1d9e2b7a6c3d8e5f1a2b3c4d5e6f
```

The pseudonym is the HMAC-SHA256 of the value with the pre-shared key (`--gdpr-psk` or `GDPR_PSK`), truncated to 16
bytes and written as 32 hexadecimal characters.

- **Deterministic.** The pseudonym is deterministic: the same value and key always give the same pseudonym. With
  another key, the pseudonyms differ; changing the key breaks the link with pseudonyms sent earlier.
- **Set your own key.** The default value in `sitekick/config.py` is a placeholder. Choose a long random value, use
  the same one on all servers of your platform, so that pseudonyms match across servers, and keep it in the
  configuration file, readable by root only (see [Installation](installation.md#configuration-file)).
- **Keep the key secret.** Whoever has the key can compute the pseudonym of a known name or email address and so
  recognise it.

### Limit what is sent

- **Pseudonymise** the owner contact name and the administrator email with `GDPR_COMPLIANT = True` in the
  configuration file.
- **Leave out the system information**: it is off by default; `--no-system-info` turns it off for a run when the
  configuration file turns it on.
- **Remove a provider module** that you do not want to run. The script loads every provider from the `providers/`
  directory, so a module that is not there does not run; for example, removing `providers/server.py` stops the
  server record. Repeat the removal after an update that brings the file back.

### Storage, retention and deletion

How long the data is stored and how it is deleted is agreed with the Sitekick operator.
