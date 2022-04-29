"""Constants"""

from typing import Final

CONFIG_FILE: Final[str] = "/etc/zone-handler.json"
DEBUG: Final[bool] = False
JOURNALCTL: Final[tuple[str, str, str, str]] = (
    "/usr/bin/journalctl",
    "--unit=named",
    "--since=-5days",
    "--utc",
)
