"""Custom types"""

from typing import Final, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

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
    server_user: str = Field(default="", validate_default=True)
    systemd_unit: str = Field(default="", validate_default=True)

    @field_validator("server_user", mode="after")
    def _default_user(cls, user: str, values: ValidationInfo) -> str:
        if not user:
            try:
                user = SERVICE_DEFAULTS[values.data["server_type"]]["user"]
            except KeyError:
                user = "nobody"
        return user

    @field_validator("systemd_unit", mode="after")
    def _default_unit(cls, systemd_unit: str, values: ValidationInfo) -> str:
        if not systemd_unit:
            try:
                systemd_unit = SERVICE_DEFAULTS[values.data["server_type"]]["unit"]
            except KeyError:
                systemd_unit = "nonexistent.service"
        return systemd_unit


class ZoneHandlerConf(BaseModel):
    """
    zone-handler.json structure
    """

    system: SystemConf
    zones: dict[str, list[str]]
