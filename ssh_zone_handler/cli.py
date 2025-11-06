"""CLI scripts entry points"""

import logging
import logging.config
import os
import pwd
import sys
from pathlib import Path
from typing import Final

import yaml
from pydantic import ValidationError

from .base import InvokeError
from .bind import BindCommand, BindSudoers
from .knot import KnotCommand, KnotSudoers
from .static import LOGCONF
from .types import ZoneHandlerConf

CONFIG_FILE: Final[Path] = Path("/etc/zone-handler.yaml")

logging.config.dictConfig(LOGCONF)


def _error_out(message: str) -> None:
    logging.critical(message)
    sys.exit(1)


def _read_config(config_file: Path) -> ZoneHandlerConf:
    with config_file.open(encoding="utf-8") as fin:
        config = ZoneHandlerConf(**yaml.safe_load(fin))

    return config


def verifier() -> None:
    """
    Entry point for the szh-verify script

    Verifies the syntax of a not-yet-installed config file

    Usage: /path/to/szh-verify /new/zone-handler.yaml
    """

    try:
        config_file = Path(sys.argv[1])
    except IndexError:
        _error_out(f"Usage: {sys.argv[0]} /path/to/zone-handler.yaml")

    try:
        _read_config(config_file)
    except (FileNotFoundError, PermissionError):
        _error_out(f"Unable to access {config_file.absolute()}")
    except yaml.YAMLError:
        _error_out(f"Malformed YAML in {config_file.absolute()}")
    except ValidationError as vle:
        _error_out(f"Invalid {config_file.absolute()}\n\n{vle}")


def sudoers(config_file: Path = CONFIG_FILE) -> None:
    """
    Entry point for the szh-sudoers script

    Outputs all the needed sudoers rules

    Usage: /path/to/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler
    """

    try:
        config: ZoneHandlerConf = _read_config(config_file)
    except (FileNotFoundError, PermissionError):
        _error_out("Unable to access server side config file")
    except yaml.YAMLError:
        _error_out("Malformed YAML in server side config file")
    except ValidationError as vle:
        _error_out(f"Invalid server side config file\n\n{vle}")

    szh: BindSudoers | KnotSudoers
    if config.system.server_type == "bind":
        szh = BindSudoers(config)
    elif config.system.server_type == "knot":
        szh = KnotSudoers(config)
    else:
        _error_out("Unsupported server configured")
    szh.generate()


def wrapper(config_file: Path = CONFIG_FILE) -> None:
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
    except yaml.YAMLError:
        _error_out("Malformed YAML in server side config file")
    except ValidationError:
        _error_out("Invalid server side config file")

    ssh_command = "help"
    try:
        ssh_command = os.environ["SSH_ORIGINAL_COMMAND"]
    except KeyError:
        pass

    szh: BindCommand | KnotCommand
    if config.system.server_type == "bind":
        szh = BindCommand(config)
    elif config.system.server_type == "knot":
        szh = KnotCommand(config)
    else:
        _error_out("Unsupported server configured")

    try:
        szh.invoke(ssh_command, username)
    except InvokeError as error:
        _error_out(str(error))
