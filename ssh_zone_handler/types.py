"""Custom types"""

from typing import Literal

from pydantic import BaseModel


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

    server: Literal["bind"]
    systemd_unit = "named.service"
    user = "bind"


class ZoneHandlerConf(BaseModel):
    """
    zone-handler.json structure
    """

    sudoers: SudoUsers
    users: dict[str, UserConf]
    service: ServiceConf
