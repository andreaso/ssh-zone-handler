"""Knot specific subclasses"""

import logging
from collections.abc import Iterator
from subprocess import CompletedProcess
from typing import Final

from .base import SshZoneCommand, SshZoneSudoers
from .types import UserConf, ZoneHandlerConf


class KnotSudoers(SshZoneSudoers):
    """Pre-generate needed Knot sudoers rules"""

    def _server_command_rules(self) -> list[str]:
        rules: list[str] = []

        for cmd in ["zone-read", "zone-retransfer"]:
            user_conf: UserConf
            for user_conf in self.config.users.values():
                zone: str
                for zone in user_conf.zones:
                    rule = (
                        f"{self.login_user}\tALL=({self.service_user}) NOPASSWD: "
                        + f"/usr/sbin/knotc {cmd} {zone}"
                    )
                    rules.append(rule)
        return rules


class KnotCommand(SshZoneCommand):
    """Runs the actual commands, for Knot"""

    def __init__(self, config: ZoneHandlerConf) -> None:
        super().__init__(config)

        self.knotc_prefix: Final[tuple[str, str, str]] = self.sudo_prefix + (
            "/usr/sbin/knotc",
        )

    @staticmethod
    def __filter_dump(content: str, zone: str) -> str:
        prefix = f"[{zone}.] "
        offset = len(prefix)
        lines = content.split("\n")
        filtered: list[str] = []

        for line in lines:
            no_prefix = line
            if line.startswith(prefix):
                no_prefix = line[offset:]
            filtered.append(no_prefix)

        return "\n".join(filtered)

    def _dump(self, zone: str) -> None:
        logging.info('Outputting "%s" zone content', zone)

        command = self.knotc_prefix + ("zone-read", zone)
        run_failure = f'Failed to dump content of zone "{zone}"'

        result: CompletedProcess[str] = self._runner(command, run_failure)
        zone_content: str = result.stdout.rstrip()
        zone_content = self.__filter_dump(zone_content, zone)

        print(zone_content)

    @staticmethod
    def _filter_logs(log_lines: list[str], zones: list[str]) -> Iterator[str]:
        line: str
        for line in log_lines:
            zone: str
            for zone in zones:
                if f"[{zone}.]" in line:
                    yield line

    def _retransfer(self, zone: str) -> None:
        logging.info('Triggering "%s" AXFR zone retransfer', zone)

        failure = f'Failed to trigger retransfer of zone "{zone}"'
        command = self.knotc_prefix + ("zone-retransfer", zone)

        self._runner(command, failure)
        print(f'Triggering retransfer of zone "{zone}"')
