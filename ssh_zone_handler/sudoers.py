"""Provides the needed sudoers rules"""

from collections.abc import KeysView

from ssh_zone_handler.constants import JOURNALCTL
from ssh_zone_handler.types import UserConf, ZoneManagerConf


def _log_rules(config: ZoneManagerConf) -> list[str]:
    users: KeysView[str] = config.users.keys()
    log_user: str = config.sudoers.logs
    command: str = " ".join(JOURNALCTL)

    rules: list[str] = []

    user: str
    for user in users:
        rule = f"{user}\tALL=({log_user}) NOPASSWD: {command}"
        rules.append(rule)

    return rules


def _rndc_rules(config: ZoneManagerConf) -> list[str]:
    rndc_user: str = config.sudoers.rndc

    rules: list[str] = []

    user: str
    user_conf: UserConf
    for user, user_conf in config.users.items():
        cmd: str
        for cmd in ["retransfer", "zonestatus"]:
            zone: str
            for zone in user_conf.zones:
                rule: str = (
                    f"{user}\tALL=({rndc_user}) NOPASSWD: /usr/sbin/rndc {cmd} {zone}"
                )
                rules.append(rule)

    return rules


def generate(config: ZoneManagerConf) -> None:
    """
    Outputs all the needed sudoers rules.

    :param config: Zone Manager Configuration
    """

    all_rules: list[str] = []

    all_rules += _log_rules(config)
    all_rules += _rndc_rules(config)

    rule: str
    for rule in all_rules:
        print(rule)
