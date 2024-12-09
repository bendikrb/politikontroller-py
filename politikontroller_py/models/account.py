from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator

from politikontroller_py.constants import (
    DEFAULT_COUNTRY,
    PHONE_NUMBER_LENGTH,
    PHONE_PREFIXES,
)
from politikontroller_py.models.common import (
    BaseModel,
    PolitiKontrollerResponse,
    StrEnum,
)
from politikontroller_py.utils import map_response_data

if TYPE_CHECKING:
    from politikontroller_py.models.common import T


def deserialize_yesno(value: str):
    return not (value == "NO" or value[:3] == "NO_")


def serialize_yesno(value: bool, suffix: str | None = None):
    if suffix is None:
        return "YES" if value else "NO"
    return suffix if value else f"NO_{suffix}"


def deserialize_bool(value: str):
    return value == "true"


def serialize_bool(value: bool):
    return "true" if value else "false"


class AuthStatus(StrEnum):
    APP_ERR = "APP_ERR"
    LOGIN_OK = "LOGIN_OK"
    LOGIN_ERROR = "LOGIN_ERROR"
    SPERRET = "SPERRET"
    NOT_ACTIVATED = "NOT_ACTIVATED"
    SKIP_AUTHENTICATION = "SKIP_AUTHENTICATION"


@dataclass(kw_only=True)
class AuthenticationResponse(PolitiKontrollerResponse):
    auth_status: AuthStatus

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="auth_status",
            include_subtypes=True,
        )

    attr_map = [
        "auth_status",
    ]

    @classmethod
    def from_response_data(cls: T, cvs: str, multiple=False) -> T | list[T]:
        data = map_response_data(cvs, cls.attr_map, multiple)
        auth_status = AuthStatus.from_str(data.get("auth_status"))
        subtypes = {
            AuthStatus.SPERRET: AuthenticationResponseBlocked,
            AuthStatus.LOGIN_OK: AuthenticationResponseOK,
            AuthStatus.LOGIN_ERROR: AuthenticationResponseError,
            AuthStatus.NOT_ACTIVATED: AuthenticationResponseNotActivated,
        }
        sub_class = subtypes.get(auth_status, cls)
        data = map_response_data(cvs, sub_class.attr_map, multiple)
        return sub_class.from_dict(data)


@dataclass
class AuthenticationResponseOK(AuthenticationResponse):
    auth_status: AuthStatus = AuthStatus.LOGIN_OK
    premium_key: str = "NO"
    user_level: int | None = None
    phone_prefix: int | None = None
    status: str | None = None
    uid: int | None = None
    nickname: str | None = None
    saphne: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_yesno,
            serialize=lambda v: serialize_yesno(v, suffix="SAPHE"),
        ),
    )
    show_regnr: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_yesno,
            serialize=lambda v: serialize_yesno(v, suffix="REGNR"),
        ),
    )
    premium_price: int | None = None
    enable_points: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_yesno,
            serialize=serialize_yesno,
        ),
    )
    enable_calls: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_yesno,
            serialize=serialize_yesno,
        ),
    )
    needs_gps: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_bool,
            serialize=serialize_bool,
        ),
    )
    gps_radius: int | None = None
    push_notification: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_bool,
            serialize=serialize_bool,
        ),
    )
    sms_notification: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_bool,
            serialize=serialize_bool,
        ),
    )
    points: int | None = None
    exchange_code: bool | None = field(
        default=None,
        metadata=field_options(
            deserialize=deserialize_bool,
            serialize=serialize_bool,
        ),
    )

    attr_map = [
        "auth_status",  # LOGIN_OK
        "premium_key",  # NO
        "user_level",  # 0
        "phone_prefix",  # 47
        "status",  # SKIP_AUTHENTICATION
        "uid",  # 1000
        None,  # 0
        "nickname",
        "saphne",  # NO_SAPHE
        "show_regnr",  # NO_REGNR
        "premium_price",  # 29
        "enable_points",  # NO
        "enable_calls",  # NO
        None,  # +47400008
        "gps_radius",  # 30
        "push_notification",  # true
        "sms_notification",  # false
        "points",  # 62
        "exchange_code",  # false
    ]


@dataclass(kw_only=True)
class AuthenticationResponseBlocked(AuthenticationResponse):
    auth_status: AuthStatus = AuthStatus.SPERRET
    block_reason: str

    attr_map = [
        "auth_status",  # SPERRET
        "block_reason",  # ...
    ]


@dataclass(kw_only=True)
class AuthenticationResponseError(AuthenticationResponse):
    auth_status: AuthStatus = AuthStatus.LOGIN_ERROR
    error: str

    attr_map = [
        "auth_status",  # LOGIN_ERROR
        "error",  # WRONG_USERNAME_OR_PASSWORD
    ]


@dataclass(kw_only=True)
class AuthenticationResponseNotActivated(AuthenticationResponse):
    auth_status: AuthStatus = AuthStatus.NOT_ACTIVATED
    uid: int

    attr_map = [
        "auth_status",  # NOT_ACTIVATED
        "uid",  # 1000
    ]


@dataclass
class AccountBase(BaseModel):
    username: str
    password: str | None = None
    country: str = DEFAULT_COUNTRY

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        d["username"] = d.get("username", "").replace(" ", "")
        return d

    @property
    def phone_number(self):
        return int(self.username[2:]) if len(self.username) > PHONE_NUMBER_LENGTH else int(self.username)

    @property
    def phone_prefix(self):
        return (
            int(self.username[:2])
            if len(self.username) > PHONE_NUMBER_LENGTH
            else PHONE_PREFIXES.get(self.country.lower())
        )


@dataclass(kw_only=True)
class Account(AccountBase):
    uid: int | None = None
    auth_status: AuthStatus | None = None
    status: str | None = None
