"""CLI scripts entry points"""

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Final, Literal

import yaml
from pydantic import ValidationError

from .base import InvokeError, SshZoneAuthorizedKeys
from .bind import BindCommand, BindSudoers
from .knot import KnotCommand, KnotSudoers
from .static import LOGCONF
from .types import ZoneHandlerConf

CONFIG_FILE: Final[Path] = Path("/etc/zone-handler.yaml")

logging.config.dictConfig(LOGCONF)


class ConfigFileError(Exception):
    """Summarizes config file parsing exceptions"""


def _error_out(message: str) -> None:
    logging.critical(message)
    sys.exit(1)


def _read_config(
    config_file: Path, errors: Literal["default", "verbose"] = "default"
) -> ZoneHandlerConf:
    try:
        with open(config_file, encoding="utf-8") as fin:
            config = ZoneHandlerConf(**yaml.safe_load(fin))
    except (FileNotFoundError, PermissionError) as fae:
        msg_fae = "Unable to access server side config file"
        raise ConfigFileError(msg_fae) from fae
    except yaml.YAMLError as yme:
        msg_yme = "Malformed YAML in server side config file"
        raise ConfigFileError(msg_yme) from yme
    except ValidationError as vle:
        msg_vle = "Invalid server side config file"
        if errors == "verbose":
            msg_vle = f"Invalid server side config file\n\n{vle}"
        raise ConfigFileError(msg_vle) from vle

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
        _read_config(config_file, errors="verbose")
    except ConfigFileError as cfe:
        _error_out(str(cfe))


def ssh_keys(config_file: Path = CONFIG_FILE) -> None:
    """
    Entry point for the szh-sshkeys script

    Used as an AuthorizedKeysCommand command

    Match User zones
         AuthorizedKeysFile none
         AuthorizedKeysCommandUser szh-sshdcmd
         AuthorizedKeysCommand /path/to/szh-sshkeys
         DisableForwarding yes
         PermitTTY no
    """

    try:
        config: ZoneHandlerConf = _read_config(config_file)
    except ConfigFileError as cfe:
        logging.debug(str(cfe))
        sys.exit(1)

    szh = SshZoneAuthorizedKeys(config)
    szh.output()


def sudoers(config_file: Path = CONFIG_FILE) -> None:
    """
    Entry point for the szh-sudoers script

    Outputs all the needed sudoers rules

    Usage: /path/to/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler
    """

    try:
        config: ZoneHandlerConf = _read_config(config_file, errors="verbose")
    except ConfigFileError as cfe:
        _error_out(str(cfe))

    szh: BindSudoers | KnotSudoers
    if config.system.server_type == "bind":
        szh = BindSudoers(config)
    elif config.system.server_type == "knot":
        szh = KnotSudoers(config)
    else:
        _error_out("Unsupported server configured")
    szh.generate()


def wrapper(config_file: Path = CONFIG_FILE) -> None:
    """Entry point for the szh-wrapper script

    Called through the authorized_keys command=, with the username
    as an argument, and with the SSH_ORIGINAL_COMMAND environment
    variable providing the user input.

    command="/path/to/szh-wrapper alice@example.com",restrict ssh-ed25519 AAAAC3NzaC1lZDI1NTE5...
    """

    try:
        username = sys.argv[1]
    except IndexError:
        _error_out(f"Usage: {sys.argv[0]} username")

    try:
        config: ZoneHandlerConf = _read_config(config_file)
    except ConfigFileError as cfe:
        _error_out(str(cfe))

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
