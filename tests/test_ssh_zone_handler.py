"""Testing top level functionality"""

# pylint: disable=missing-function-docstring,line-too-long

import os
import pwd

import pytest
from pydantic import ValidationError

from ssh_zone_handler.bind import BindCommand
from ssh_zone_handler.cli import _read_config, sudoers, wrapper
from ssh_zone_handler.knot import KnotCommand


def mock_pwd_name(name):
    return pwd.struct_passwd((name, None, None, None, None, None, None))


def test_cli_read_config():
    example_config = _read_config("./tests/data/bind-example-config.yaml")
    assert example_config == {
        "system": {
            "log_access_user": "log-viewer",
            "server_type": "bind",
            "server_user": "bind",
            "systemd_unit": "named.service",
        },
        "zones": {
            "alice": ["example.com", "example.net"],
            "bob": ["example.org"],
        },
    }

    alternative_config = _read_config("./tests/data/bind-alternative-config.yaml")
    assert alternative_config == {
        "system": {
            "log_access_user": "odin",
            "server_type": "bind",
            "server_user": "named",
            "systemd_unit": "bind9.service",
        },
        "zones": {
            "bob": ["example.org"],
        },
    }

    knot_config = _read_config("./tests/data/knot-example-config.yaml")
    assert knot_config == {
        "system": {
            "log_access_user": "log-viewer",
            "server_type": "knot",
            "server_user": "knot",
            "systemd_unit": "knot.service",
        },
        "zones": {
            "alice": ["example.com", "example.net"],
            "bob": ["example.org"],
        },
    }

    with pytest.raises(ValidationError):
        _read_config("./tests/data/outdated-config.yaml")


def test_cli_zone_sudoers(caplog, capsys):
    sudoers("./tests/data/bind-example-config.yaml")
    captured_expected = capsys.readouterr()

    assert captured_expected.out == "\n".join(
        [
            "alice\tALL=(log-viewer) NOPASSWD: /usr/bin/journalctl --unit=named.service --since=-5days --utc",  # noqa: E501
            "bob\tALL=(log-viewer) NOPASSWD: /usr/bin/journalctl --unit=named.service --since=-5days --utc",  # noqa: E501
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.com",
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.net",
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.com",
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.net",
            "bob\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.org",
            "bob\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.org\n",
        ]
    )

    caplog.clear()
    sudoers("./tests/data/knot-example-config.yaml")
    captured_knot_expected = capsys.readouterr()

    assert captured_knot_expected.out == "\n".join(
        [
            "alice\tALL=(log-viewer) NOPASSWD: /usr/bin/journalctl --unit=knot.service --since=-5days --utc",  # noqa: E501
            "bob\tALL=(log-viewer) NOPASSWD: /usr/bin/journalctl --unit=knot.service --since=-5days --utc",  # noqa: E501
            "alice\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-read example.com",
            "alice\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-read example.net",
            "alice\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-retransfer example.com",
            "alice\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-retransfer example.net",
            "alice\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-status example.com",
            "alice\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-status example.net",
            "bob\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-read example.org",
            "bob\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-retransfer example.org",
            "bob\tALL=(knot) NOPASSWD: /usr/sbin/knotc zone-status example.org\n",
        ]
    )

    caplog.clear()
    with pytest.raises(SystemExit):
        sudoers("./tests/data/outdated-config.yaml")
    captured_outdated = caplog.text
    assert (
        "Invalid server side config file\n\n1 validation error for ZoneHandlerConf"
        in captured_outdated
    )


def test_cli_zone_wrapper(caplog, capsys, mocker):
    mocker.patch("pwd.getpwuid", return_value=mock_pwd_name("alice"))

    os.environ["SSH_ORIGINAL_COMMAND"] = "list"
    wrapper("./tests/data/bind-example-config.yaml")
    captured_passing = capsys.readouterr()
    assert captured_passing.out == "example.com\nexample.net\n"

    caplog.clear()
    os.environ["SSH_ORIGINAL_COMMAND"] = "sing"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/bind-example-config.yaml")
    captured_invalid = caplog.text
    assert captured_invalid == 'Invalid command, try "help"\n'

    caplog.clear()
    os.environ["SSH_ORIGINAL_COMMAND"] = "status"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/bind-example-config.yaml")
    captured_no_zone = caplog.text
    assert captured_no_zone == "No valid zone provided\n"

    caplog.clear()
    os.environ["SSH_ORIGINAL_COMMAND"] = "logs example.org"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/bind-example-config.yaml")
    captured_wrong_zone = caplog.text
    assert captured_wrong_zone == "No valid zone provided\n"

    caplog.clear()
    os.environ["SSH_ORIGINAL_COMMAND"] = "list"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/outdated-config.yaml")
    captured_outdated = caplog.text
    assert captured_outdated == "Invalid server side config file\n"

    caplog.clear()
    mocker.patch("pwd.getpwuid", return_value=mock_pwd_name("mallory"))
    os.environ["SSH_ORIGINAL_COMMAND"] = "help"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/bind-example-config.yaml")
    captured_unconf_user = caplog.text
    assert captured_unconf_user == 'No zones configured for user "mallory"\n'


def test_bind_log_filtering():
    pre_filtered_file_net = "./tests/data/filtered-named-example-net.txt"
    with open(pre_filtered_file_net, encoding="utf-8") as fin:
        pre_filtered_data_net = fin.read().rstrip()

    pre_filtered_file_com_net = "./tests/data/filtered-named-example-com-net.txt"
    with open(pre_filtered_file_com_net, encoding="utf-8") as fin:
        pre_filtered_data_com_net = fin.read().rstrip()

    log_file = "./tests/data/journald-named.txt"
    with open(log_file, encoding="utf-8") as fin:
        log_data = fin.read()

    log_lines = log_data.split("\n")

    zones = ["example.net"]
    filtered = []
    # pylint: disable=protected-access
    for line in BindCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == pre_filtered_data_net.split("\n")

    zones = ["example.com", "example.net"]
    filtered = []
    # pylint: disable=protected-access
    for line in BindCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == pre_filtered_data_com_net.split("\n")


def test_knot_log_filtering():
    pre_filtered_file_net = "./tests/data/filtered-knot-example-net.txt"
    with open(pre_filtered_file_net, encoding="utf-8") as fin:
        pre_filtered_data_net = fin.read().rstrip()

    pre_filtered_file_com_net = "./tests/data/filtered-knot-example-com-net.txt"
    with open(pre_filtered_file_com_net, encoding="utf-8") as fin:
        pre_filtered_data_com_net = fin.read().rstrip()

    log_file = "./tests/data/journald-knot.txt"
    with open(log_file, encoding="utf-8") as fin:
        log_data = fin.read()

    log_lines = log_data.split("\n")

    zones = ["example.net"]
    filtered = []
    # pylint: disable=protected-access
    for line in KnotCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == pre_filtered_data_net.split("\n")

    zones = ["example.com", "example.net"]
    filtered = []
    # pylint: disable=protected-access
    for line in KnotCommand._filter_logs(log_lines, zones):
        filtered.append(line)
    assert filtered == pre_filtered_data_com_net.split("\n")
