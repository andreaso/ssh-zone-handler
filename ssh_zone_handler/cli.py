"""CLI scripts entry points"""

import json
import logging
import logging.config
import os
import pwd
import sys
from typing import Final

from pydantic import ValidationError

from ssh_zone_handler.commands import InvokeError, SshZoneCommand, SshZoneSudoers
from ssh_zone_handler.static import LOGCONF
from ssh_zone_handler.types import ZoneHandlerConf

CONFIG_FILE: Final[str] = "/etc/zone-handler.json"

logging.config.dictConfig(LOGCONF)


def _error_out(message: str) -> None:
    logging.critical(message)
    sys.exit(1)


def _read_config(config_file: str) -> ZoneHandlerConf:
    with open(config_file, encoding="utf-8") as fin:
        config = ZoneHandlerConf(**json.load(fin))

    return config


def sudoers(config_file: str = CONFIG_FILE) -> None:
    """
    Entry point for the szh-sudoers script

    Outputs all the needed sudoers rules

    Usage: /path/to/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler
    """

    try:
        config: ZoneHandlerConf = _read_config(config_file)
    except (FileNotFoundError, PermissionError):
        _error_out("Unable to access server side config file")
    except json.decoder.JSONDecodeError:
        _error_out("Malformed JSON in server side config file")
    except ValidationError:
        _error_out("Invalid server side config file")

    szh = SshZoneSudoers(config)
    szh.generate()


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
        config: ZoneHandlerConf = _read_config(config_file)
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

    szh = SshZoneCommand(config)
    try:
        szh.invoke(ssh_command, username)
    except InvokeError as error:
        _error_out(str(error))
