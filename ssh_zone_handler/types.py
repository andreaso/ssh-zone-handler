"""Custom types"""

from typing import Literal

from pydantic import BaseModel, validator

SERVICE_DEFAULTS = {
    "bind": {
        "unit": "named.service",
        "user": "bind",
    },
    "knot": {
        "unit": "knot.service",
        "user": "knot",
    },
}


class SudoUsers(BaseModel):
    """
    Subset of ZoneHandlerConf
    """

    logs: str


class UserConf(BaseModel):
    """
    Subset of ZoneHandlerConf
    """

    zones: list[str]


class ServiceConf(BaseModel):
    """
    Subset of ZoneHandlerConf
    """

    server: Literal["bind", "knot"]
    systemd_unit = ""
    user = ""

    @validator("systemd_unit", always=True)
    # pylint: disable=no-self-argument
    def _default_unit(cls, systemd_unit: str, values: dict[str, str]) -> str:
        if not systemd_unit:
            systemd_unit = SERVICE_DEFAULTS[values["server"]]["unit"]
        return systemd_unit

    @validator("user", always=True)
    # pylint: disable=no-self-argument
    def _default_user(cls, user: str, values: dict[str, str]) -> str:
        if not user:
            user = SERVICE_DEFAULTS[values["server"]]["user"]
        return user


class ZoneHandlerConf(BaseModel):
    """
    zone-handler.json structure
    """

    sudoers: SudoUsers
    users: dict[str, UserConf]
    service: ServiceConf
