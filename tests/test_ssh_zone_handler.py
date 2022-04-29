"""Testing top level functionality"""

# pylint: disable=missing-function-docstring,line-too-long

import os
import pwd

import pytest
from pydantic import ValidationError

from ssh_zone_handler.cli import _read_config, sudoers, wrapper


def mock_pwd_name(name):
    return pwd.struct_passwd((name, None, None, None, None, None, None))


def test_cli_read_config():
    example_config = _read_config("./tests/data/example-config.json")
    assert example_config == {
        "sudoers": {
            "logs": "log-viewer",
            "rndc": "bind",
        },
        "users": {
            "alice": {"zones": ["example.com", "example.net"]},
            "bob": {"zones": ["example.org"]},
        },
        "zone_paths": "/var/cache/bind/{zone_name}.zone",
    }

    alternative_config = _read_config("./tests/data/alternative-config.json")
    assert alternative_config == {
        "sudoers": {
            "logs": "odin",
            "rndc": "named",
        },
        "users": {
            "bob": {"zones": ["example.org"]},
        },
        "zone_paths": "/var/cache/bind/db.{zone_name}",
    }

    with pytest.raises(ValidationError):
        _read_config("./tests/data/outdated-config.json")


def test_cli_zone_sudoers(capsys):
    sudoers("./tests/data/example-config.json")
    captured_expected = capsys.readouterr()

    assert captured_expected.out == "\n".join(
        [
            "alice\tALL=(log-viewer) NOPASSWD: /usr/bin/journalctl --unit=named --since=-5days --utc",  # noqa: E501
            "bob\tALL=(log-viewer) NOPASSWD: /usr/bin/journalctl --unit=named --since=-5days --utc",  # noqa: E501
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.com",
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.net",
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.com",
            "alice\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.net",
            "bob\tALL=(bind) NOPASSWD: /usr/sbin/rndc retransfer example.org",
            "bob\tALL=(bind) NOPASSWD: /usr/sbin/rndc zonestatus example.org\n",
        ]
    )

    with pytest.raises(SystemExit):
        sudoers("./tests/data/outdated-config.json")
    captured_outdated = capsys.readouterr()
    assert captured_outdated.err == "Invalid server side config file\n"


def test_cli_zone_wrapper(capsys, mocker):
    mocker.patch("pwd.getpwuid", return_value=mock_pwd_name("alice"))

    os.environ["SSH_ORIGINAL_COMMAND"] = "list"
    wrapper("./tests/data/example-config.json")
    captured_passing = capsys.readouterr()
    assert captured_passing.out == "example.com\nexample.net\n"

    os.environ["SSH_ORIGINAL_COMMAND"] = "sing"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/example-config.json")
    captured_invalid = capsys.readouterr()
    assert captured_invalid.err == 'Invalid command, try "help"\n'

    os.environ["SSH_ORIGINAL_COMMAND"] = "logs"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/example-config.json")
    captured_no_zone = capsys.readouterr()
    assert captured_no_zone.err == "No valid zone provided\n"

    os.environ["SSH_ORIGINAL_COMMAND"] = "logs example.org"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/example-config.json")
    captured_wrong_zone = capsys.readouterr()
    assert captured_wrong_zone.err == "No valid zone provided\n"

    os.environ["SSH_ORIGINAL_COMMAND"] = "list"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/outdated-config.json")
    captured_outdated = capsys.readouterr()
    assert captured_outdated.err == "Invalid server side config file\n"

    mocker.patch("pwd.getpwuid", return_value=mock_pwd_name("mallory"))
    os.environ["SSH_ORIGINAL_COMMAND"] = "help"
    with pytest.raises(SystemExit):
        wrapper("./tests/data/example-config.json")
    captured_unconf_user = capsys.readouterr()
    assert captured_unconf_user.err == 'No zones configured for user "mallory"\n'
