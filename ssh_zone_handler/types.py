"""Custom types"""

from pydantic import BaseModel


class SudoUsers(BaseModel):
    """
    Subset of ZoneManagerConf
    """

    logs: str
    rndc = "bind"


class UserConf(BaseModel):
    """
    Subset of ZoneManagerConf
    """

    zones: list[str]


class ZoneManagerConf(BaseModel):
    """
    zone-handler.json structure
    """

    sudoers: SudoUsers
    users: dict[str, UserConf]
