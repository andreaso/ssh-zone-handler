"""BIND specific subclasses"""

import logging
import re
from collections.abc import Iterator
from subprocess import CompletedProcess
from typing import Final

from .base import InvokeError, SshZoneCommand, SshZoneSudoers
from .types import UserConf, ZoneHandlerConf


class BindSudoers(SshZoneSudoers):
    """Pre-generate needed BIND sudoers rules"""

    def _server_command_rules(self) -> list[str]:
        rules: list[str] = []
        for cmd in ["retransfer", "zonestatus"]:
            user_conf: UserConf
            for user_conf in self.config.users.values():
                zone: str
                for zone in user_conf.zones:
                    rule = (
                        f"{self.login_user}\tALL=({self.service_user}) NOPASSWD: "
                        + f"/usr/sbin/rndc {cmd} {zone}"
                    )
                    rules.append(rule)
        return rules


class BindCommand(SshZoneCommand):
    """Runs the actual commands, for BIND"""

    def __init__(self, config: ZoneHandlerConf) -> None:
        super().__init__(config)

        self.rndc_prefix: Final[tuple[str, str, str]] = self.sudo_prefix + (
            "/usr/sbin/rndc",
        )

    def __lookup(self, zone: str, failure: str) -> str | None:
        zone_file: str | None = None
        command = self.rndc_prefix + ("zonestatus", zone)

        result: CompletedProcess[str] = self._runner(command, failure)

        line: str
        matched: re.Match[str] | None
        pattern = re.compile(r"^([^:]+): (.+)$")
        for line in result.stdout.split("\n"):
            matched = pattern.match(line)
            if matched and matched.group(1) == "files":
                zone_file = matched.group(2)
                break

        return zone_file

    def _dump(self, zone: str) -> None:
        logging.info('Outputting "%s" zone content', zone)

        lookup_failure = f'Failed to lookup zone file for zone "{zone}"'
        zone_file: str | None = self.__lookup(zone, lookup_failure)
        if not zone_file:
            raise InvokeError(lookup_failure)

        command = (
            "/usr/bin/named-compilezone",
            "-f",
            "raw",
            "-o",
            "-",
            zone,
            zone_file,
        )

        run_failure = f'Failed to dump content of zone "{zone}"'
        result: CompletedProcess[str] = self._runner(command, run_failure)
        zone_content: str = result.stdout.rstrip()

        print(zone_content)

    @staticmethod
    def _filter_logs(log_lines: list[str], zones: list[str]) -> Iterator[str]:
        line: str
        for line in log_lines:
            zone: str
            for zone in zones:
                if (
                    f"zone {zone}/IN" in line
                    or f"'retransfer {zone}'" in line
                    or f"'{zone}/AXFR/IN'" in line
                    or f"'{zone}/IN'" in line
                    or f"'{zone}'" in line
                ):
                    yield line

    def _retransfer(self, zone: str) -> None:
        logging.info('Triggering "%s" AXFR zone retransfer', zone)

        failure = f'Failed to trigger retransfer of zone "{zone}"'
        command = self.rndc_prefix + ("retransfer", zone)

        self._runner(command, failure)
        print(f'Triggering retransfer of zone "{zone}"')
