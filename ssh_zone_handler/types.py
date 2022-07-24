"""Custom types"""

from typing import Literal

from pydantic import BaseModel, validator

SERVICE_DEFAULTS = {
    "bind": {
        "unit": "named.service",
    },
    "knot": {
        "unit": "knot.service",
    },
}


class SudoUsers(BaseModel):
    """
    Subset of ZoneHandlerConf
    """

    logs: str
    rndc = "bind"


class UserConf(BaseModel):
    """
    Subset of ZoneHandlerConf
    """

    zones: list[str]


class ServiceConf(BaseModel):
    """
    Subset of ZoneHandlerConf
    """

    daemon: Literal["bind", "knot"]
    systemd_unit: str = ""

    @validator("systemd_unit", always=True)
    # pylint: disable=no-self-argument
    def _default_unit(cls, systemd_unit: str, values: dict[str, str]) -> str:
        if not systemd_unit:
            systemd_unit = SERVICE_DEFAULTS[values["daemon"]]["unit"]
        return systemd_unit


class ZoneHandlerConf(BaseModel):
    """
    zone-handler.json structure
    """

    sudoers: SudoUsers
    users: dict[str, UserConf]
    service: ServiceConf
