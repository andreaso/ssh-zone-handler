"""Custom types"""

from typing import Final, Literal

from pydantic import BaseModel, validator

SERVICE_DEFAULTS: Final[dict[str, dict[str, str]]] = {
    "bind": {
        "unit": "named.service",
        "user": "bind",
    },
    "knot": {
        "unit": "knot.service",
        "user": "knot",
    },
}


class SystemConf(BaseModel):
    """
    Subset of ZoneHandlerConf
    """

    log_access_user: str
    server_type: Literal["bind", "knot"]
    server_user = ""
    systemd_unit = ""

    @validator("server_user", always=True)
    # pylint: disable=no-self-argument
    def _default_user(cls, user: str, values: dict[str, str]) -> str:
        if not user:
            try:
                user = SERVICE_DEFAULTS[values["server_type"]]["user"]
            except KeyError:
                user = "nobody"
        return user

    @validator("systemd_unit", always=True)
    # pylint: disable=no-self-argument
    def _default_unit(cls, systemd_unit: str, values: dict[str, str]) -> str:
        if not systemd_unit:
            try:
                systemd_unit = SERVICE_DEFAULTS[values["server_type"]]["unit"]
            except KeyError:
                systemd_unit = "nonexistent.service"
        return systemd_unit


class ZoneHandlerConf(BaseModel):
    """
    zone-handler.json structure
    """

    system: SystemConf
    zones: dict[str, list[str]]
