"""Command functionality"""

import re
import sys
from collections.abc import KeysView, Sequence
from subprocess import CalledProcessError, CompletedProcess, run
from typing import Final, Optional

from ssh_zone_handler.types import UserConf, ZoneHandlerConf

JOURNALCTL: Final[tuple[str, str, str, str]] = (
    "/usr/bin/journalctl",
    "--unit=named",
    "--since=-5days",
    "--utc",
)


class InvokeError(Exception):
    """Used to propagate an error to the top level wrapper method"""


class SshZoneHandler:
    """This is where all the magic happens"""

    def __init__(self, config: ZoneHandlerConf):
        self.config: ZoneHandlerConf = config
        self.debug: Final[bool] = config.debug
        self.log_user: Final[str] = config.sudoers.logs
        self.rndc_user: Final[str] = config.sudoers.rndc

    def __log_rules(self) -> list[str]:
        users: KeysView[str] = self.config.users.keys()
        command: str = " ".join(JOURNALCTL)
        rules: list[str] = []

        user: str
        for user in users:
            rule = f"{user}\tALL=({self.log_user}) NOPASSWD: {command}"
            rules.append(rule)

        return rules

    def __rndc_rules(self) -> list[str]:
        rules: list[str] = []

        user: str
        user_conf: UserConf
        for user, user_conf in self.config.users.items():
            cmd: str
            for cmd in ["retransfer", "zonestatus"]:
                zone: str
                for zone in user_conf.zones:
                    rule: str = (
                        f"{user}\tALL=({self.rndc_user}) NOPASSWD: "
                        + f"/usr/sbin/rndc {cmd} {zone}"
                    )
                    rules.append(rule)

        return rules

    def __zone_list(self, username: str) -> Sequence[str]:
        user_zones: Sequence[str] = ()

        try:
            user_zones = tuple(self.config.users[username].zones)
        except KeyError:
            pass

        return user_zones

    @staticmethod
    def __parse(
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

    def __runner(self, command: Sequence[str], failure: str) -> CompletedProcess[str]:
        try:
            result = run(command, capture_output=True, check=True, text=True)
        except (FileNotFoundError, CalledProcessError) as err:
            if self.debug:
                print(f"{type(err).__name__}: {str(err)}", file=sys.stderr)
            raise InvokeError(failure) from err

        return result

    def __lookup(self, zone: str, failure: str) -> Optional[str]:
        zone_file: Optional[str] = None

        command: Sequence[str] = (
            "/usr/bin/sudo",
            f"--user={self.rndc_user}",
            "/usr/sbin/rndc",
            "zonestatus",
            zone,
        )

        result: CompletedProcess[str] = self.__runner(command, failure)

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

    @staticmethod
    def __usage() -> None:
        print("usage: command [ZONE]")
        print()
        print("help\t\t\tDisplay this help message")
        print("list\t\t\tList available zones")
        print("dump ZONE\t\tOutput full content of ZONE")
        print("logs ZONE\t\tOutput the last five days' log entries for ZONE")
        print("retransfer ZONE\t\tTrigger a full (AXFR) retransfer of ZONE")
        print("status ZONE\t\tShow ZONE status")

    def __dump(self, zone: str) -> None:
        lookup_failure = f'Failed to lookup zone file for zone "{zone}"'
        zone_file: Optional[str] = self.__lookup(zone, lookup_failure)

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

        result: CompletedProcess[str] = self.__runner(command, run_failure)

        zone_content: str = result.stdout.rstrip()
        print(zone_content)

    def __logs(self, zone: str) -> None:
        failure = f'Failed to output log lines for zone "{zone}"'
        command = ("/usr/bin/sudo", f"--user={self.log_user}") + JOURNALCTL

        result: CompletedProcess[str] = self.__runner(command, failure)

        line: str
        for line in result.stdout.split("\n"):
            if (
                f"zone {zone}/IN" in line
                or f"'retransfer {zone}'" in line
                or f"'{zone}/IN'" in line
                or f"'{zone}'" in line
            ):
                print(line)

    def __retransfer(self, zone: str) -> None:
        failure = f'Failed to trigger retransfer of zone "{zone}"'
        command = (
            "/usr/bin/sudo",
            f"--user={self.rndc_user}",
            "/usr/sbin/rndc",
            "retransfer",
            zone,
        )
        self.__runner(command, failure)
        print(f'Triggering retransfer of zone "{zone}"')

    def __status(self, zone: str) -> None:
        failure = f'Failed to display status for zone "{zone}"'
        command = (
            "/usr/bin/sudo",
            f"--user={self.rndc_user}",
            "/usr/sbin/rndc",
            "zonestatus",
            zone,
        )

        result: CompletedProcess[str] = self.__runner(command, failure)

        zone_status: str = result.stdout.rstrip()
        print(zone_status)

    def generate(self) -> None:
        """Outputs all the needed sudoers rules."""

        all_rules: list[str] = []
        all_rules += self.__log_rules()
        all_rules += self.__rndc_rules()

        rule: str
        for rule in all_rules:
            print(rule)

    def invoke(self, ssh_command: str, username: str) -> None:
        """
        Pick what, if any, command to invoke.

        :param ssh_command: The full SSH_ORIGINAL_COMMAND
        :param username: Current user, executing the program
        """

        user_zones: Sequence[str] = self.__zone_list(username)

        if not user_zones:
            raise InvokeError(f'No zones configured for user "{username}"')

        command: Optional[str]
        zone: Optional[str]
        command, zone = self.__parse(ssh_command, user_zones)

        if not command:
            raise InvokeError('Invalid command, try "help"')

        if command == "help":
            self.__usage()
        elif command == "list":
            uzn: str
            for uzn in user_zones:
                print(uzn)
        elif not zone:
            raise InvokeError("No valid zone provided")
        elif command == "dump":
            self.__dump(zone)
        elif command == "logs":
            self.__logs(zone)
        elif command == "retransfer":
            self.__retransfer(zone)
        elif command == "status":
            self.__status(zone)
