---
title: Testing
---

# Testing

There are three ways to check the script: the unit tests, the `test` command, and a local echo server that shows the
requests the script sends. Test on a development machine or a test server, and keep test data out of the queue of a
production server.

## Unit tests

The unit tests are in `tests/` and use pytest. Install pytest in a virtual environment on your development machine
(the servers do not need it) and run, from the root of the repository:

```bash
pytest -q
```

`tests/test_cli_config.py` covers the command line and the configuration:

- the defaults of the options equal the values in `sitekick/config.py`;
- options given on the command line end up in `sitekick.config`, for every combination of the on/off options;
- a configuration file is read from a directory and from a file path, and its values become the defaults of the
  options;
- an option on the command line takes precedence over the configuration file;
- the automatic-update setting: no network request for updates is made when it is off.

`tests/conftest.py` puts the root of the repository on the Python path, so the tests import `sitekick` and
`providers` directly.

## The test command

`python3 domains-to-sitekick.py test plesk` prints what a provider produces, even on a machine where the provider
does not apply; it does not queue or push records. Run it before the first `send`, and see
[Commands and configuration](usage.md#test) for the arguments, the output and the `debug` provider.

## A local echo server

`test_server.py` is a small HTTP server, standard library only. It listens on port 8000 of all network interfaces,
prints every JSON body it receives and answers with status 200 and an echo of the request. Run it only on a test
machine. Start it in one terminal:

```bash
python3 test_server.py
```

Stop it with Ctrl+C. In a second terminal, send to it:

```bash
python3 domains-to-sitekick.py --queue-path /tmp/sitekick/test-queue --sitekick-url http://127.0.0.1:8000/ send
```

The echo server prints each batch as the platform would receive it: the `data` list with the records and their
`meta` blocks. Because it answers 200, the script treats every batch as accepted and empties the test queue.

## Safe practice

- **Use a separate queue directory.** All runs share the queue directory, and a run pushes every file it finds there.
  With the default queue, a test run would send records that a scheduled run left behind to your test URL, and a
  scheduled run would send your test records to Sitekick. Pass `--queue-path` with a directory of its own, as in the
  example above.
- **Name the test URL explicitly.** Without `--sitekick-url` or a configuration file, `send` posts to the Sitekick
  push endpoint.
- **Expect the `debug` provider to run.** A test `send` runs every provider that applies, including `debug`: it
  retrieves the diagnostic commands from the Sitekick debug URL (`SITEKICK_DEBUG_URL`), runs them and sends their
  output to your test URL (see [Diagnostic mode](index.md#diagnostic-mode)).
- **Do not leave test configuration behind.** Options passed on the command line apply to that run only; a test
  setting in `/etc/server-to-sitekick/config.py` applies to every scheduled run.
- **Use example values** such as `example.com` when you share test output or add it to a pull request.
