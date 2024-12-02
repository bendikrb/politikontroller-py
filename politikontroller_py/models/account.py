from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

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

if TYPE_CHECKING:
    from politikontroller_py.models.common import T


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
    premium_key: str = "NO"
    user_level: int
    phone_prefix: int
    status: str | None = None
    uid: int
    nickname: str | None = None
    saphne: Literal["SAPHE", "NO_SAPHE"] | None = None
    show_regnr: Literal["REGNR", "NO_REGNR"] | None = None
    premium_price: int | None = None
    enable_points: Literal["YES", "NO"] | None = None
    enable_calls: Literal["YES", "NO"] | None = None
    needs_gps: bool | None = None
    gps_radius: int | None = None
    push_notification: bool | None = None
    sms_notification: bool | None = None
    points: int | None = None
    exchange_code: bool | None = None

    attr_map = [
        "auth_status",
        # 0  LoginStatus:  APP_ERR|LOGIN_OK|NOT_ACTIVATED|SPERRET|LOGIN_ERROR
        "premium_key",  # 1  PremiumKey: str | Literal["NO"]
        "user_level",  # 2  user_level: int
        "phone_prefix",  # 3  RetningsKode: int
        "status",  # 4  status: str
        "uid",  # 5  brukerId: int
        None,  # 6
        "nickname",  # 7  kallenavn: str
        "saphne",  # 8  saphne: Literal["SAPHE"] | None
        "show_regnr",  # 9  vis_regnr: Literal["REGNR"] | None
        "premium_price",  # 10 premium_price: int
        "enable_points",  # 11 enable_points: str
        "enable_calls",  # 12 enable_calls: str
        None,  # 13 needs_gps: bool
        "gps_radius",  # 14 gps_radius: int
        "push_notification",  # 15 push_varsling: bool
        "sms_notification",  # 16 sms_varsling: bool
        "points",  # 17 DinePoeng: int
        "exchange_code",  # 18 LosInnKode: bool
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

    def get_query_params(self):
        """Get query params."""
        return {
            "retning": self.phone_prefix,
            "telefon": self.phone_number,
            "passord": self.password,
        }


@dataclass(kw_only=True)
class Account(AccountBase):
    uid: int | None = None
    auth_status: AuthStatus | None = None
    status: str | None = None
