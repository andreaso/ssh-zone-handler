"""Custom types"""

from typing import Annotated, Final, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

InternalUser = Annotated[str, Field(pattern=r"^[a-z][a-z0-9.@_-]*[a-z0-9]$")]
SystemUser = Annotated[str, Field(pattern=r"^[a-z_][a-z0-9_-]*[a-z0-9]$")]
ServiceUnit = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]*[a-z0-9]\.service$")]
FwdZone = Annotated[str, Field(pattern=r"^([a-z0-9][a-z0-9-]+[a-z0-9]\.)+[a-z]+$")]
Ptr4Zone = Annotated[str, Field(pattern=r"^[0-9/]+\.([0-9]+\.)+in-addr\.arpa$")]
Ptr6Zone = Annotated[str, Field(pattern=r"^([a-f0-9]\.)+ip6\.arpa$")]
Zone = FwdZone | Ptr4Zone | Ptr6Zone

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


class SystemConf(BaseModel, extra="forbid", frozen=True):
    """
    Subset of ZoneHandlerConf
    """

    log_access_user: SystemUser
    server_type: Literal["bind", "knot"]
    server_user: SystemUser = Field(default="", validate_default=True)
    systemd_unit: ServiceUnit = Field(default="", validate_default=True)

    @field_validator("server_user", mode="before")
    def _default_user(cls, user: str, values: ValidationInfo) -> str:
        if not user:
            try:
                user = SERVICE_DEFAULTS[values.data["server_type"]]["user"]
            except KeyError:
                user = "nobody"
        return user

    @field_validator("systemd_unit", mode="before")
    def _default_unit(cls, systemd_unit: str, values: ValidationInfo) -> str:
        if not systemd_unit:
            try:
                systemd_unit = SERVICE_DEFAULTS[values.data["server_type"]]["unit"]
            except KeyError:
                systemd_unit = "nonexistent.service"
        return systemd_unit


class UserConf(BaseModel, extra="forbid", frozen=True):
    """
    Subset of ZoneHandlerConf
    """

    zones: list[Zone]


class ZoneHandlerConf(BaseModel, extra="forbid", frozen=True):
    """
    zone-handler.yaml structure
    """

    system: SystemConf
    users: dict[InternalUser, UserConf]
