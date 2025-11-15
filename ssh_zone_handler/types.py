"""Custom types"""

from typing import Annotated, Final, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
from typing_extensions import Self

InternalUser = Annotated[str, Field(pattern=r"^[a-z][a-z0-9.@_-]*[a-z0-9]$")]
SystemUser = Annotated[str, Field(pattern=r"^[a-z_][a-z0-9_-]*[a-z0-9]$")]
ServiceUnit = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]*[a-z0-9]\.service$")]
FwdZone = Annotated[str, Field(pattern=r"^([a-z0-9][a-z0-9-]+[a-z0-9]\.)+[a-z]+$")]
Ptr4Zone = Annotated[str, Field(pattern=r"^[0-9/]+\.([0-9]+\.)+in-addr\.arpa$")]
Ptr6Zone = Annotated[str, Field(pattern=r"^([a-f0-9]\.)+ip6\.arpa$")]
Zone = FwdZone | Ptr4Zone | Ptr6Zone

SSHKey = Annotated[str, Field(pattern=r"^(ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNT|ecdsa-sha2-nistp384 AAAAE2VjZHNhLXNoYTItbmlzdHAzOD|ecdsa-sha2-nistp521 AAAAE2VjZHNhLXNoYTItbmlzdHA1Mj|sk-ecdsa-sha2-nistp256@openssh.com AAAAInNrLWVjZHNhLXNoYTItbmlzdHAyNTZAb3BlbnNzaC5jb2|ssh-ed25519 AAAAC3NzaC1lZDI1NTE5|sk-ssh-ed25519@openssh.com AAAAGnNrLXNzaC1lZDI1NTE5QG9wZW5zc2guY29t|ssh-rsa AAAAB3NzaC1yc2)[0-9A-Za-z+/]+[=]{0,3}(\s.*)?$")]  # fmt: skip

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

    journalctl_user: SystemUser
    login_user: SystemUser
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

    ssh_keys: list[SSHKey] = []
    zones: list[Zone]

    @field_validator("ssh_keys", mode="after")
    def _clean_ssh_keys(cls, ssh_keys: list[SSHKey]) -> list[SSHKey]:
        cleaned_keys: list[SSHKey] = []
        for ssh_key in ssh_keys:
            cleaned_keys.append(" ".join(ssh_key.split()[:2]))
        return cleaned_keys


class ZoneHandlerConf(BaseModel, extra="forbid", frozen=True):
    """
    zone-handler.yaml structure
    """

    system: SystemConf
    users: dict[InternalUser, UserConf]

    @model_validator(mode="after")
    def _check_duplicate_keys(self) -> Self:
        all_the_keys: list[SSHKey] = []
        for user_conf in self.users.values():
            all_the_keys.extend(user_conf.ssh_keys)

        if sorted(all_the_keys) != sorted(set(all_the_keys)):
            raise ValueError("Duplicate ssh keys not allowed")

        return self
