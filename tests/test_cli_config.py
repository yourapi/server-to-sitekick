import runpy
import sys
import tempfile
from pathlib import Path
from itertools import product

import json
import runpy
import socket

import urllib.request
import pytest

from sitekick import config
from sitekick import commandline
from providers import plesk


def _reset_parser_defaults():
    commandline.parser.set_defaults(
        config_path=config.CONFIG_PATH,
        queue_path=config.QUEUE_PATH,
        sitekick_url=config.SITEKICK_PUSH_URL,
        enable_autoupdate=config.ENABLE_AUTOUPDATE,
        system_info=config.SYSTEM_INFO,
        gdpr_compliant=config.GDPR_COMPLIANT,
        gdpr_psk=config.GDPR_PSK,
    )


@pytest.fixture(autouse=True)
def _restore_config():
    snapshot = {
        "CONFIG_PATH": config.CONFIG_PATH,
        "QUEUE_PATH": config.QUEUE_PATH,
        "SITEKICK_PUSH_URL": config.SITEKICK_PUSH_URL,
        "ENABLE_AUTOUPDATE": config.ENABLE_AUTOUPDATE,
        "SYSTEM_INFO": config.SYSTEM_INFO,
        "GDPR_COMPLIANT": config.GDPR_COMPLIANT,
        "GDPR_PSK": config.GDPR_PSK,
    }
    yield
    for key, value in snapshot.items():
        setattr(config, key, value)
    _reset_parser_defaults()


def test_parser_defaults():
    args = commandline.parser.parse_args([])
    assert args.config_path == config.CONFIG_PATH
    assert args.queue_path == config.QUEUE_PATH
    assert args.sitekick_url == config.SITEKICK_PUSH_URL
    assert args.enable_autoupdate == config.ENABLE_AUTOUPDATE
    assert args.system_info == config.SYSTEM_INFO
    assert args.gdpr_compliant == config.GDPR_COMPLIANT
    assert args.gdpr_psk == config.GDPR_PSK


def test_cli_overrides_apply_to_config(monkeypatch):
    monkeypatch.setattr(commandline, "send", lambda *args: None)
    args = commandline.parser.parse_args([
        "--config-path", "/tmp/custom-config",
        "--queue-path", "/tmp/queue",
        "--sitekick-url", "http://localhost:9000/push",
        "--enable-autoupdate",
        "--no-system-info",
        "--gdpr-compliant",
        "--gdpr-psk", "test-psk",
        "send",
    ])
    commandline.execute(args)

    assert config.CONFIG_PATH == "/tmp/custom-config"
    assert config.QUEUE_PATH == "/tmp/queue"
    assert config.SITEKICK_PUSH_URL == "http://localhost:9000/push"
    assert config.ENABLE_AUTOUPDATE is True
    assert config.SYSTEM_INFO is False
    assert config.GDPR_COMPLIANT is True
    assert config.GDPR_PSK == "test-psk"


@pytest.mark.parametrize(
    "args,expected_autoupdate,expected_queue,expected_url",
    [
        ([], None, None, None),
        (["--enable-autoupdate"], True, None, None),
        (["--queue-path", "/tmp/queue-x"], None, "/tmp/queue-x", None),
        (["--sitekick-url", "http://localhost:8080/push"], None, None, "http://localhost:8080/push"),
        (["--enable-autoupdate", "--queue-path", "/tmp/queue-y", "--sitekick-url", "http://localhost:8081/push"],
         True, "/tmp/queue-y", "http://localhost:8081/push"),
    ],
)
def test_cli_overrides_autoupdate_queue_url(monkeypatch, args, expected_autoupdate, expected_queue, expected_url):
    monkeypatch.setattr(commandline, "send", lambda *args: None)
    parsed = commandline.parser.parse_args(args + ["send"])
    commandline.execute(parsed)

    if expected_autoupdate is None:
        expected_autoupdate = config.ENABLE_AUTOUPDATE
    if expected_queue is None:
        expected_queue = config.QUEUE_PATH
    if expected_url is None:
        expected_url = config.SITEKICK_PUSH_URL

    assert config.ENABLE_AUTOUPDATE is expected_autoupdate
    assert config.QUEUE_PATH == expected_queue
    assert config.SITEKICK_PUSH_URL == expected_url


@pytest.mark.parametrize(
    "enable_autoupdate,system_info,gdpr_compliant",
    list(product([False, True], [False, True], [False, True])),
)
def test_all_boolean_flag_combinations_apply(monkeypatch, enable_autoupdate, system_info, gdpr_compliant):
    monkeypatch.setattr(commandline, "send", lambda *args: None)

    argv = [
        "--queue-path", "/tmp/queue-combo",
        "--sitekick-url", "http://localhost:9999/push",
        "--gdpr-psk", "combo-psk",
    ]

    if enable_autoupdate:
        argv.append("--enable-autoupdate")

    argv.append("--system-info" if system_info else "--no-system-info")
    argv.append("--gdpr-compliant" if gdpr_compliant else "--no-gdpr-compliant")

    parsed = commandline.parser.parse_args(argv + ["send"])
    commandline.execute(parsed)

    assert config.ENABLE_AUTOUPDATE is enable_autoupdate
    assert config.SYSTEM_INFO is system_info
    assert config.GDPR_COMPLIANT is gdpr_compliant
    assert config.GDPR_PSK == "combo-psk"
    assert config.QUEUE_PATH == "/tmp/queue-combo"
    assert config.SITEKICK_PUSH_URL == "http://localhost:9999/push"


def test_config_file_loads_from_path(monkeypatch):
    monkeypatch.setattr(commandline, "send", lambda *args: None)
    sys_argv_backup = list(sys.argv)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            config_file = temp_dir_path / "config.py"
            config_file.write_text(
                "QUEUE_PATH = '/tmp/queue-from-file'\n"
                "SITEKICK_PUSH_URL = 'http://localhost:7000/push'\n"
                "ENABLE_AUTOUPDATE = False\n"
                "SYSTEM_INFO = False\n"
                "GDPR_COMPLIANT = True\n"
                "GDPR_PSK = 'file-psk'\n"
            )
            script_path = Path(__file__).resolve().parents[1] / "domains-to-sitekick.py"
            sys.argv = [
                str(script_path),
                "--config-path", str(config_file),
                "send",
            ]
            runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = sys_argv_backup

    assert config.CONFIG_PATH == str(config_file)
    assert config.QUEUE_PATH == "/tmp/queue-from-file"
    assert config.SITEKICK_PUSH_URL == "http://localhost:7000/push"
    assert config.ENABLE_AUTOUPDATE is False
    assert config.SYSTEM_INFO is False
    assert config.GDPR_COMPLIANT is True
    assert config.GDPR_PSK == "file-psk"


def test_config_file_updates_parsed_defaults_when_passed_as_config_path(monkeypatch):
    """When --config-path points to a config.py file, non-specified CLI options should use loaded values."""
    captured = {"args": None}

    def fake_execute(args):
        captured["args"] = args

    monkeypatch.setattr(commandline, "execute", fake_execute)

    sys_argv_backup = list(sys.argv)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            config_file = temp_dir_path / "config.py"
            config_file.write_text(
                "QUEUE_PATH = '/tmp/queue-from-file-defaults'\n"
                "SITEKICK_PUSH_URL = 'http://localhost:7010/push'\n"
                "ENABLE_AUTOUPDATE = False\n"
                "SYSTEM_INFO = False\n"
                "GDPR_COMPLIANT = True\n"
                "GDPR_PSK = 'defaults-psk'\n"
            )
            script_path = Path(__file__).resolve().parents[1] / "domains-to-sitekick.py"
            sys.argv = [
                str(script_path),
                "--config-path", str(config_file),
                "send",
            ]
            runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = sys_argv_backup

    assert captured["args"] is not None
    assert captured["args"].config_path == str(config_file)
    assert captured["args"].queue_path == "/tmp/queue-from-file-defaults"
    assert captured["args"].sitekick_url == "http://localhost:7010/push"
    assert captured["args"].enable_autoupdate is False
    assert captured["args"].system_info is False
    assert captured["args"].gdpr_compliant is True
    assert captured["args"].gdpr_psk == "defaults-psk"


def test_config_directory_loads_from_path(monkeypatch):
    monkeypatch.setattr(commandline, "send", lambda *args: None)
    sys_argv_backup = list(sys.argv)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            (temp_dir_path / "config.py").write_text(
                "QUEUE_PATH = '/tmp/queue-from-dir'\n"
                "SITEKICK_PUSH_URL = 'http://localhost:7001/push'\n"
                "ENABLE_AUTOUPDATE = False\n"
                "SYSTEM_INFO = True\n"
                "GDPR_COMPLIANT = False\n"
                "GDPR_PSK = 'dir-psk'\n"
            )
            script_path = Path(__file__).resolve().parents[1] / "domains-to-sitekick.py"
            sys.argv = [
                str(script_path),
                "--config-path", str(temp_dir_path),
                "send",
            ]
            runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = sys_argv_backup

    assert config.CONFIG_PATH == str(temp_dir_path)
    assert config.QUEUE_PATH == "/tmp/queue-from-dir"
    assert config.SITEKICK_PUSH_URL == "http://localhost:7001/push"
    assert config.ENABLE_AUTOUPDATE is False
    assert config.SYSTEM_INFO is True
    assert config.GDPR_COMPLIANT is False
    assert config.GDPR_PSK == "dir-psk"


def test_config_file_then_cli_overrides_take_precedence(monkeypatch):
    """Values from config file should load first; explicit CLI options must override them."""
    monkeypatch.setattr(commandline, "send", lambda *args: None)
    sys_argv_backup = list(sys.argv)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            config_file = temp_dir_path / "config.py"
            config_file.write_text(
                "QUEUE_PATH = '/tmp/queue-from-file'\n"
                "SITEKICK_PUSH_URL = 'http://localhost:7002/from-file'\n"
                "ENABLE_AUTOUPDATE = False\n"
                "SYSTEM_INFO = True\n"
                "GDPR_COMPLIANT = True\n"
                "GDPR_PSK = 'file-psk'\n"
            )
            script_path = Path(__file__).resolve().parents[1] / "domains-to-sitekick.py"
            sys.argv = [
                str(script_path),
                "--config-path", str(config_file),
                "--queue-path", "/tmp/queue-from-cli",
                "--sitekick-url", "http://localhost:7002/from-cli",
                "--no-system-info",
                "--no-gdpr-compliant",
                "--gdpr-psk", "cli-psk",
                "send",
            ]
            runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = sys_argv_backup

    assert config.CONFIG_PATH == str(config_file)
    assert config.QUEUE_PATH == "/tmp/queue-from-cli"
    assert config.SITEKICK_PUSH_URL == "http://localhost:7002/from-cli"
    assert config.SYSTEM_INFO is False
    assert config.GDPR_COMPLIANT is False
    assert config.GDPR_PSK == "cli-psk"


def _run_domains_to_sitekick_with_config(monkeypatch, config_text: str):
    """
    Helper: writes a temp config.py, sets sys.argv, runs domains-to-sitekick.py via runpy,
    then restores sys.argv.
    """
    monkeypatch.setattr(socket, "gethostname", lambda: "not-local-testing-host")
    monkeypatch.setattr(plesk, "is_server_type", lambda: False)
    
    sys_argv_backup = list(sys.argv)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            config_file = temp_dir_path / "config.py"
            config_file.write_text(config_text)

            script_path = Path(__file__).resolve().parents[1] / "domains-to-sitekick.py"
            sys.argv = [str(script_path), "--config-path", str(config_file), "send"]

            runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = sys_argv_backup


def test_autoupdate_disabled_does_not_hit_network(monkeypatch):
    """
    When ENABLE_AUTOUPDATE=False, the script should NOT call urllib.request.urlopen.

    This works even though domains-to-sitekick.py does:
      from urllib.request import urlopen

    because we patch urllib.request.urlopen BEFORE runpy.run_path executes the script,
    so the script binds the patched function.
    """
    # Avoid the early-return path in load_code()
    monkeypatch.setattr(socket, "gethostname", lambda: "not-145-131-8-226")

    calls = {"count": 0}

    def fake_urlopen(req):
        calls["count"] += 1
        raise AssertionError("urlopen() should not be called when autoupdate is disabled")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    _run_domains_to_sitekick_with_config(monkeypatch,
        "ENABLE_AUTOUPDATE = False\n"
        "QUEUE_PATH = '/tmp/q'\n"
        "SITEKICK_PUSH_URL = 'http://localhost/push'\n"
    )

    assert calls["count"] == 0


def test_autoupdate_enabled_hits_network_path(monkeypatch, tmp_path):
    """
    Paired test: when ENABLE_AUTOUPDATE=True, we expect the script to attempt to call urlopen.

    We return fake responses:
    - first urlopen() call: returns JSON list with 1 file
    - second urlopen() call: returns the content bytes for that file

    This proves the monkeypatch is effective and the update path is reachable.
    """
    monkeypatch.setattr(socket, "gethostname", lambda: "not-145-131-8-226")

    calls = {"count": 0}

    class Resp:
        def __init__(self, b: bytes):
            self._b = b

        def read(self):
            return self._b

    def fake_urlopen(req):
        calls["count"] += 1

        # 1) CODE_ENDPOINT request -> return list of files
        if calls["count"] == 1:
            files = [
                {
                    "path": "x",
                    "name": "y.txt",
                    "_timestamp_": "2026-02-06T12:00:00.000+00:00",
                    "content": "http://example.invalid/content",
                }
            ]
            return Resp(json.dumps(files).encode("utf-8"))

        # 2) content request -> return bytes
        return Resp(b"hello from fake urlopen")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    # We want root_path to be writable so the script can write downloaded files.
    # If domains-to-sitekick.py uses root_path = Path(__file__).parent.parent,
    # it writes into your repo. That's annoying in tests.
    #
    # If your script supports --config-path pointing at a directory and reads config.py,
    # you can set a config variable that influences root_path, but you said you can't change code.
    # So this test assumes either:
    # - the script writes into a temp dir because it is run from temp, OR
    # - the download write is best-effort (errors are caught) and won't fail the test.
    #
    # If it DOES write into repo and you want to avoid it, we can patch Path(__file__) via runpy,
    # but that's messier. Start with this; if it creates a stray file, tell me and we’ll harden it.

    _run_domains_to_sitekick_with_config(monkeypatch,
        "ENABLE_AUTOUPDATE = True\n"
        "QUEUE_PATH = '/tmp/q'\n"
        "SITEKICK_PUSH_URL = 'http://localhost/push'\n"
    )

    assert calls["count"] >= 1