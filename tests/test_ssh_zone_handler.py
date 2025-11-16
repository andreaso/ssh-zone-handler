# ruff: noqa: ANN001, ANN201, S101
"""Testing top level functionality"""

import os
import sys
from pathlib import Path

import pytest

from ssh_zone_handler.bind import BindCommand
from ssh_zone_handler.cli import (
    ConfigFileError,
    _read_config,
    ssh_keys,
    sudoers,
    wrapper,
)
from ssh_zone_handler.knot import KnotCommand


def test_cli_read_config():
    example_config = _read_config(Path("./tests/data/bind-example-config.yaml"))
    assert example_config.model_dump() == {
        "system": {
            "journalctl_user": "szh-logviewer",
            "login_user": "zones",
            "server_type": "bind",
            "server_user": "bind",
            "systemd_unit": "named.service",
        },
        "users": {
            "alice": {
                "ssh_keys": [
                    "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIGlLAm/yjw76GuHsUDlqEJMrIRiyHSMlXlx/XlpRn1dfAAAABHNzaDo=",
                    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIOy9uTo12niUl2JCWUebyzr/5pMa64BuFc/0nGjtQad",
                ],
                "zones": ["example.com", "example.net"],
            },
            "bob": {
                "ssh_keys": [
                    "sk-ecdsa-sha2-nistp256@openssh.com AAAAInNrLWVjZHNhLXNoYTItbmlzdHAyNTZAb3BlbnNzaC5jb20AAAAIbmlzdHAyNTYAAABBBPnGjVz9axrV3stm+5onXYSO/MIOdggKBw5Y5jYJReqwnkIuQ+OMME6oQUuvev+hCURpnKBlfC8zcHRKWUYFF1IAAAAEc3NoOg==",
                ],
                "zones": ["example.org"],
            },
        },
    }

    alternative_config = _read_config(Path("./tests/data/bind-alternative-config.yaml"))
    assert alternative_config.model_dump() == {
        "system": {
            "journalctl_user": "odin",
            "login_user": "zones",
            "server_type": "bind",
            "server_user": "named",
            "systemd_unit": "bind9.service",
        },
        "users": {
            "bob": {
                "ssh_keys": [],
                "zones": ["example.org"],
            },
        },
    }

    knot_config = _read_config(Path("./tests/data/knot-example-config.yaml"))
    assert knot_config.model_dump() == {
        "system": {
            "journalctl_user": "szh-logviewer",
            "login_user": "zones",
            "server_type": "knot",
            "server_user": "knot",
            "systemd_unit": "knot.service",
        },
        "users": {
            "alice": {
                "ssh_keys": [
                    "sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIGlLAm/yjw76GuHsUDlqEJMrIRiyHSMlXlx/XlpRn1dfAAAABHNzaDo=",
                    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIOy9uTo12niUl2JCWUebyzr/5pMa64BuFc/0nGjtQad",
                ],
                "zones": ["example.com", "example.net"],
            },
            "bob": {
                "ssh_keys": [
                    "sk-ecdsa-sha2-nistp256@openssh.com AAAAInNrLWVjZHNhLXNoYTItbmlzdHAyNTZAb3BlbnNzaC5jb20AAAAIbmlzdHAyNTYAAABBBPnGjVz9axrV3stm+5onXYSO/MIOdggKBw5Y5jYJReqwnkIuQ+OMME6oQUuvev+hCURpnKBlfC8zcHRKWUYFF1IAAAAEc3NoOg==",
                ],
                "zones": ["example.org"],
            },
        },
    }

    with pytest.raises(ConfigFileError):
        _read_config(Path("./tests/data/outdated-config.yaml"))


def test_cli_zone_ssh_keys(caplog, capsys):
    wrapper = Path(sys.argv[0]).absolute().parent / "szh-wrapper"

    ssh_keys(Path("./tests/data/bind-example-config.yaml"))
    captured_expected = capsys.readouterr()

    assert captured_expected.out == "\n".join(
        [
            f'command="{wrapper} alice",restrict sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29tAAAAIGlLAm/yjw76GuHsUDlqEJMrIRiyHSMlXlx/XlpRn1dfAAAABHNzaDo=',
            f'command="{wrapper} alice",restrict ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIOy9uTo12niUl2JCWUebyzr/5pMa64BuFc/0nGjtQad',
            f'command="{wrapper} bob",restrict sk-ecdsa-sha2-nistp256@openssh.com AAAAInNrLWVjZHNhLXNoYTItbmlzdHAyNTZAb3BlbnNzaC5jb20AAAAIbmlzdHAyNTYAAABBBPnGjVz9axrV3stm+5onXYSO/MIOdggKBw5Y5jYJReqwnkIuQ+OMME6oQUuvev+hCURpnKBlfC8zcHRKWUYFF1IAAAAEc3NoOg==\n',
        ]
    )

    caplog.clear()
    ssh_keys(Path("./tests/data/bind-alternative-config.yaml"))
    captured_alternate_expected = capsys.readouterr()

    assert captured_alternate_expected.out == "\n".join([])

    caplog.clear()
    with pytest.raises(SystemExit):
        sudoers(Path("./tests/data/duplicate-ssh-keys-config.yaml"))


def test_cli_zone_sudoers(caplog, capsys):
    sudoers(Path("./tests/data/bind-example-config.yaml"))
    captured_expected = capsys.readouterr()

    assert captured_expected.out == "\n".join(
        [
            "zones\tALL=(szh-logviewer) NOPASSWD: /usr/bin/journalctl --unit=named.service --since=-5days --utc",
            "zones\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.com",
            "zones\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.net",
            "zones\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.org",
            "zones\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.com",
            "zones\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.net",
            "zones\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.org\n",
        ]
    )

    caplog.clear()
    sudoers(Path("./tests/data/knot-example-config.yaml"))
    captured_knot_expected = capsys.readouterr()

    assert captured_knot_expected.out == "\n".join(
        [
            "zones\tALL=(szh-logviewer) NOPASSWD: /usr/bin/journalctl --unit=knot.service --since=-5days --utc",
            "zones\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-read example.com",
            "zones\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-read example.net",
            "zones\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-read example.org",
            "zones\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-retransfer example.com",
            "zones\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-retransfer example.net",
            "zones\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-retransfer example.org\n",
        ]
    )

    caplog.clear()
    with pytest.raises(SystemExit):
        sudoers(Path("./tests/data/outdated-config.yaml"))
    captured_outdated = caplog.text
    assert (
        "Invalid server side config file\n\n5 validation errors for ZoneHandlerConf"
        in captured_outdated
    )


def test_cli_zone_wrapper(caplog, capsys, mocker):
    mocker.patch("sys.argv", ["_", "alice"])

    os.environ["SSH_ORIGINAL_COMMAND"] = "list"
    wrapper(Path("./tests/data/bind-example-config.yaml"))
    captured_passing = capsys.readouterr()
    assert captured_passing.out == "example.com\nexample.net\n"

    caplog.clear()
    os.environ["SSH_ORIGINAL_COMMAND"] = "sing"
    with pytest.raises(SystemExit):
        wrapper(Path("./tests/data/bind-example-config.yaml"))
    captured_invalid = caplog.text
    assert captured_invalid == 'Invalid command, try "help"\n'

    caplog.clear()
    os.environ["SSH_ORIGINAL_COMMAND"] = "logs example.org"
    with pytest.raises(SystemExit):
        wrapper(Path("./tests/data/bind-example-config.yaml"))
    captured_wrong_zone = caplog.text
    assert captured_wrong_zone == "No valid zone provided\n"

    caplog.clear()
    os.environ["SSH_ORIGINAL_COMMAND"] = "list"
    with pytest.raises(SystemExit):
        wrapper(Path("./tests/data/outdated-config.yaml"))
    captured_outdated = caplog.text
    assert captured_outdated == "Invalid server side config file\n"

    caplog.clear()
    mocker.patch("sys.argv", ["_", "mallory"])
    os.environ["SSH_ORIGINAL_COMMAND"] = "help"
    with pytest.raises(SystemExit):
        wrapper(Path("./tests/data/bind-example-config.yaml"))
    captured_unconf_user = caplog.text
    assert captured_unconf_user == 'No zones configured for user "mallory"\n'


def test_bind_log_filtering():
    filtered_file_net = Path("./tests/data/filtered-named-example-net.txt")
    filtered_data_net = filtered_file_net.read_text(encoding="utf-8").rstrip()

    filtered_file_com_net = Path("./tests/data/filtered-named-example-com-net.txt")
    filtered_data_com_net = filtered_file_com_net.read_text(encoding="utf-8").rstrip()

    log_file = Path("./tests/data/journald-named.txt")
    log_data = log_file.read_text(encoding="utf-8")
    log_lines = log_data.split("\n")

    zones = ["example.net"]
    filtered = []
    for line in BindCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == filtered_data_net.split("\n")

    zones = ["example.com", "example.net"]
    filtered = []
    for line in BindCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == filtered_data_com_net.split("\n")


def test_knot_log_filtering():
    filtered_file_net = Path("./tests/data/filtered-knot-example-net.txt")
    filtered_data_net = filtered_file_net.read_text(encoding="utf-8").rstrip()

    filtered_file_com_net = Path("./tests/data/filtered-knot-example-com-net.txt")
    filtered_data_com_net = filtered_file_com_net.read_text(encoding="utf-8").rstrip()

    log_file = Path("./tests/data/journald-knot.txt")
    log_data = log_file.read_text(encoding="utf-8")
    log_lines = log_data.split("\n")

    zones = ["example.net"]
    filtered = []
    for line in KnotCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == filtered_data_net.split("\n")

    zones = ["example.com", "example.net"]
    filtered = []
    for line in KnotCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == filtered_data_com_net.split("\n")
