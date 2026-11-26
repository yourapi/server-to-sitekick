import runpy
import sys
import tempfile
from pathlib import Path
from itertools import product

import pytest

from sitekick import config
from sitekick import commandline


def _reset_parser_defaults():
    commandline.parser.set_defaults(
        config_path=config.CONFIG_PATH,
        queue_path=config.QUEUE_PATH,
        sitekick_url=config.SITEKICK_PUSH_URL,
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
    assert args.system_info == config.SYSTEM_INFO
    assert args.gdpr_compliant == config.GDPR_COMPLIANT
    assert args.gdpr_psk == config.GDPR_PSK


def test_cli_overrides_apply_to_config(monkeypatch):
    monkeypatch.setattr(commandline, "send", lambda *args: None)
    args = commandline.parser.parse_args([
        "--config-path", "/tmp/custom-config",
        "--queue-path", "/tmp/queue",
        "--sitekick-url", "http://localhost:9000/push",
        "--no-system-info",
        "--gdpr-compliant",
        "--gdpr-psk", "test-psk",
        "send",
    ])
    commandline.execute(args)

    assert config.CONFIG_PATH == "/tmp/custom-config"
    assert config.QUEUE_PATH == "/tmp/queue"
    assert config.SITEKICK_PUSH_URL == "http://localhost:9000/push"
    assert config.SYSTEM_INFO is False
    assert config.GDPR_COMPLIANT is True
    assert config.GDPR_PSK == "test-psk"


@pytest.mark.parametrize(
    "args,expected_queue,expected_url",
    [
        ([], None, None),
        (["--queue-path", "/tmp/queue-x"], "/tmp/queue-x", None),
        (["--sitekick-url", "http://localhost:8080/push"], None, "http://localhost:8080/push"),
        (["--queue-path", "/tmp/queue-y", "--sitekick-url", "http://localhost:8081/push"],
         "/tmp/queue-y", "http://localhost:8081/push"),
    ],
)
def test_cli_overrides_queue_url(monkeypatch, args, expected_queue, expected_url):
    monkeypatch.setattr(commandline, "send", lambda *args: None)
    parsed = commandline.parser.parse_args(args + ["send"])
    commandline.execute(parsed)

    if expected_queue is None:
        expected_queue = config.QUEUE_PATH
    if expected_url is None:
        expected_url = config.SITEKICK_PUSH_URL

    assert config.QUEUE_PATH == expected_queue
    assert config.SITEKICK_PUSH_URL == expected_url


@pytest.mark.parametrize(
    "system_info,gdpr_compliant",
    list(product([False, True], [False, True])),
)
def test_all_boolean_flag_combinations_apply(monkeypatch, system_info, gdpr_compliant):
    monkeypatch.setattr(commandline, "send", lambda *args: None)

    argv = [
        "--queue-path", "/tmp/queue-combo",
        "--sitekick-url", "http://localhost:9999/push",
        "--gdpr-psk", "combo-psk",
    ]

    argv.append("--system-info" if system_info else "--no-system-info")
    argv.append("--gdpr-compliant" if gdpr_compliant else "--no-gdpr-compliant")

    parsed = commandline.parser.parse_args(argv + ["send"])
    commandline.execute(parsed)

    assert config.SYSTEM_INFO is system_info
    assert config.GDPR_COMPLIANT is gdpr_compliant
    assert config.GDPR_PSK == "combo-psk"
    assert config.QUEUE_PATH == "/tmp/queue-combo"
    assert config.SITEKICK_PUSH_URL == "http://localhost:9999/push"


@pytest.mark.parametrize("argv", [["debug"], ["--enable-autoupdate", "send"]])
def test_removed_command_and_option_are_rejected(argv):
    """The diagnostic mode and the automatic update were removed in version 0.3."""
    with pytest.raises(SystemExit):
        commandline.parser.parse_args(argv)


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
