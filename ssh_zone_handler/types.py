"""Custom types"""

from pydantic import BaseModel


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


class ZoneHandlerConf(BaseModel):
    """
    zone-handler.json structure
    """

    sudoers: SudoUsers
    users: dict[str, UserConf]
