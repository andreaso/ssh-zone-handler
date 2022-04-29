"""CLI scripts entry points"""

import json
import os
import pwd
import sys

from pydantic import ValidationError

from ssh_zone_handler.commands import InvokeError, invoke
from ssh_zone_handler.constants import CONFIG_FILE
from ssh_zone_handler.sudoers import generate
from ssh_zone_handler.types import ZoneManagerConf


def _error_out(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def _read_config(config_file: str) -> ZoneManagerConf:
    with open(config_file, encoding="utf-8") as fin:
        config = ZoneManagerConf(**json.load(fin))

    return config


def sudoers(config_file: str = CONFIG_FILE) -> None:
    """
    Entry point for the szh-sudoers script

    Outputs all the needed sudoers rules

    Usage: /path/to/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler
    """

    try:
        config: ZoneManagerConf = _read_config(config_file)
    except (FileNotFoundError, PermissionError):
        _error_out("Unable to access server side config file")
    except json.decoder.JSONDecodeError:
        _error_out("Malformed JSON in server side config file")
    except ValidationError:
        _error_out("Invalid server side config file")

    generate(config)


def wrapper(config_file: str = CONFIG_FILE) -> None:
    """
    Entry point for the szh-wrapper script

    Called by the sshd ForceCommand, getting all its input from the
    SSH_ORIGINAL_COMMAND environment variable

    Match User alice,bob
        ForceCommand /path/to/szh-wrapper
        PermitTTY no
        AllowTcpForwarding no
        X11Forwarding no
    """

    username: str = pwd.getpwuid(os.getuid()).pw_name
    try:
        config: ZoneManagerConf = _read_config(config_file)
    except (FileNotFoundError, PermissionError):
        _error_out("Unable to access server side config file")
    except json.decoder.JSONDecodeError:
        _error_out("Malformed JSON in server side config file")
    except ValidationError:
        _error_out("Invalid server side config file")

    ssh_command = "help"
    try:
        ssh_command = os.environ["SSH_ORIGINAL_COMMAND"]
    except KeyError:
        pass

    try:
        invoke(ssh_command, username, config)
    except InvokeError as error:
        _error_out(str(error))
