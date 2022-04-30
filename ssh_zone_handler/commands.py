"""Command functionality"""

import re
import sys
from collections.abc import Sequence
from subprocess import CalledProcessError, CompletedProcess, run
from typing import Optional

from ssh_zone_handler.constants import DEBUG, JOURNALCTL
from ssh_zone_handler.types import ZoneManagerConf


class InvokeError(Exception):
    """Used to propagate an error to the top level wrapper method"""


def _zone_list(username: str, config: ZoneManagerConf) -> Sequence[str]:
    user_zones: Sequence[str] = ()

    try:
        user_zones = tuple(config.users[username].zones)
    except KeyError:
        pass

    return user_zones


def _parse(
    ssh_command: str, user_zones: Sequence[str]
) -> tuple[Optional[str], Optional[str]]:

    args: list[str] = ssh_command.split()
    command: Optional[str] = None
    zone: Optional[str] = None

    if args[0] in ["help", "list", "dump", "logs", "retransfer", "status"]:
        command = args[0]

    try:
        if args[1] in user_zones:
            zone = args[1]
    except IndexError:
        pass

    return command, zone


def _runner(command: Sequence[str], failure: str) -> CompletedProcess[str]:
    try:
        result = run(command, capture_output=True, check=True, text=True)
    except (FileNotFoundError, CalledProcessError) as err:
        if DEBUG:
            print(f"{type(err).__name__}: {str(err)}", file=sys.stderr)
        raise InvokeError(failure) from err

    return result


def _lookup(zone: str, rndc_user: str, failure: str) -> Optional[str]:
    zone_file: Optional[str] = None

    command: Sequence[str] = (
        "/usr/bin/sudo",
        f"--user={rndc_user}",
        "/usr/sbin/rndc",
        "zonestatus",
        zone,
    )

    result: CompletedProcess[str] = _runner(command, failure)

    line: str
    matched: Optional[re.Match[str]]
    pattern = re.compile(r"^([^:]+): (.+)$")
    for line in result.stdout.split("\n"):
        matched = pattern.match(line)
        if matched:
            if matched.group(1) == "files":
                zone_file = matched.group(2)
                break

    return zone_file


def _usage() -> None:
    print("usage: command [ZONE]")
    print()
    print("help\t\t\tDisplay this help message")
    print("list\t\t\tList available zones")
    print("dump ZONE\t\tOutput full content of ZONE")
    print("logs ZONE\t\tOutput the last five days' log entries for ZONE")
    print("retransfer ZONE\t\tTrigger a full (AXFR) retransfer of ZONE")
    print("status ZONE\t\tShow ZONE status")


def _dump(zone: str, rndc_user: str) -> None:
    lookup_failure = f'Failed to lookup zone file for zone "{zone}"'
    zone_file: Optional[str] = _lookup(zone, rndc_user, lookup_failure)
    if not zone_file:
        raise InvokeError(lookup_failure)

    run_failure = f'Failed to dump content of zone "{zone}"'
    command = (
        "/usr/bin/named-compilezone",
        "-f",
        "raw",
        "-o",
        "-",
        zone,
        zone_file,
    )

    result: CompletedProcess[str] = _runner(command, run_failure)

    zone_content: str = result.stdout.rstrip()
    print(zone_content)


def _logs(zone: str, log_user: str) -> None:
    failure = f'Failed to output log lines for zone "{zone}"'
    command = ("/usr/bin/sudo", f"--user={log_user}") + JOURNALCTL

    result: CompletedProcess[str] = _runner(command, failure)

    line: str
    for line in result.stdout.split("\n"):
        if f"zone {zone}/IN" in line or f"'{zone}/IN'" in line or f"'{zone}'" in line:
            print(line)


def _retransfer(zone: str, rndc_user: str) -> None:
    failure = f'Failed to trigger retransfer of zone "{zone}"'
    command = (
        "/usr/bin/sudo",
        f"--user={rndc_user}",
        "/usr/sbin/rndc",
        "retransfer",
        zone,
    )

    _runner(command, failure)
    print(f'Triggering retransfer of zone "{zone}"')


def _status(zone: str, rndc_user: str) -> None:
    failure = f'Failed to display status for zone "{zone}"'
    command = (
        "/usr/bin/sudo",
        f"--user={rndc_user}",
        "/usr/sbin/rndc",
        "zonestatus",
        zone,
    )

    result: CompletedProcess[str] = _runner(command, failure)

    zone_status: str = result.stdout.rstrip()
    print(zone_status)


def invoke(ssh_command: str, username: str, config: ZoneManagerConf) -> None:
    """
    Pick what, if any, command to invoke.

    :param ssh_command: The full SSH_ORIGINAL_COMMAND
    :param username: Current user, executing the program
    :param config: Zone Manager Configuration
    """

    user_zones: Sequence[str] = _zone_list(username, config)

    if not user_zones:
        raise InvokeError(f'No zones configured for user "{username}"')

    command: Optional[str]
    zone: Optional[str]
    command, zone = _parse(ssh_command, user_zones)

    log_user: str = config.sudoers.logs
    rndc_user: str = config.sudoers.rndc

    if not command:
        raise InvokeError('Invalid command, try "help"')

    if command == "help":
        _usage()
    elif command == "list":
        uzn: str
        for uzn in user_zones:
            print(uzn)
    elif not zone:
        raise InvokeError("No valid zone provided")
    elif command == "dump":
        _dump(zone, rndc_user)
    elif command == "logs":
        _logs(zone, log_user)
    elif command == "retransfer":
        _retransfer(zone, rndc_user)
    elif command == "status":
        _status(zone, rndc_user)
