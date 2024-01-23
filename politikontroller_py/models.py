"""Politikontroller models."""
from __future__ import annotations

from abc import ABC
from datetime import datetime
from enum import Enum, auto
import logging
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, field_validator

from .constants import DEFAULT_COUNTRY, PHONE_NUMBER_LENGTH, PHONE_PREFIXES
from .utils import map_response_data, parse_time_format

_LOGGER = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
class StrEnum(str, Enum):
    """A string enumeration of type `(str, Enum)`.
    All members are compared via `upper()`. Defaults to UNKNOWN.
    """

    def __eq__(self, other: str) -> bool:
        other = other.upper()
        return super().__eq__(other)

    @classmethod
    def _missing_(cls, value) -> str:
        has_unknown = False
        for member in cls:
            if member.name.upper() == "unknown":
                has_unknown = True
            if member.name.upper() == value.upper():
                return member
        if has_unknown:
            _LOGGER.warning("'%s' is not a valid '%s'", value, cls.__name__)
            return cls.UNKNOWN
        raise ValueError(f"'{value}' is not a valid {cls.__name__}")


class AuthStatus(StrEnum):
    APP_ERR = 'APP_ERR'
    LOGIN_OK = 'LOGIN_OK'
    LOGIN_ERROR = 'LOGIN_ERROR'
    SPERRET = 'SPERRET'
    NOT_ACTIVATED = 'NOT_ACTIVATED'
    SKIP_AUTHENTICATION = 'SKIP_AUTHENTICATION'


class ExchangeStatus(StrEnum):
    EXCHANGE_OK = auto()


class PolitiKontrollerRequest(BaseModel):
    pass


class PolitiKontrollerResponse(BaseModel, ABC):
    model_config = ConfigDict(use_enum_values=True)

    attr_map: ClassVar[list[str]]

    @classmethod
    def from_response_data(
        cls,
        data: str,
        multiple=False
    ) -> list[dict[str, str]] | dict[str, str]:
        """Convert a cvs-like string into dictionaries."""
        return map_response_data(data, cls.attr_map, multiple)


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
        'auth_status',
        # 0  LoginStatus:  APP_ERR|LOGIN_OK|NOT_ACTIVATED|SPERRET|LOGIN_ERROR
        'premium_key',  # 1  PremiumKey: str | Literal["NO"]
        'user_level',  # 2  user_level: int
        'phone_prefix',  # 3  RetningsKode: int
        'status',  # 4  status: str
        'uid',  # 5  brukerId: int
        None,  # 6
        'nickname',  # 7  kallenavn: str
        'saphne',  # 8  saphne: Literal["SAPHE"] | None
        'show_regnr',  # 9  vis_regnr: Literal["REGNR"] | None
        'premium_price',  # 10 premium_price: int
        'enable_points',  # 11 enable_points: str
        'enable_calls',  # 12 enable_calls: str
        None,  # 13 needs_gps: bool
        'gps_radius',  # 14 gps_radius: int
        'push_notification',  # 15 push_varsling: bool
        'sms_notification',  # 16 sms_varsling: bool
        'points',  # 17 DinePoeng: int
        'exchange_code',  # 18 LosInnKode: bool
    ]


class PoliceControlTypeEnum(str, Enum):
    SPEED_TRAP = "Fartskontroll"
    BEHAVIOUR = "Belte/mobil"
    TECHNICAL = "Teknisk"
    TRAFFIC_INFO = "Trafikk info"
    TRAFFIC_MESSAGE = "Trafikkmelding"
    OBSERVATION = "Observasjon"
    CUSTOMS = "Toll/grense"
    WEIGHT = "Vektkontroll"
    UNKNOWN = "Ukjent"
    CIVIL_POLICE = "Sivilpoliti"
    MC_CONTROL = "Mopedkontroll"
    BOAT_PATROL = "Politibåten"


class BaseResponseModel(BaseModel):
    pass


class AuthenticationRequest(PolitiKontrollerRequest):
    username: str
    password: str


# noinspection PyNestedDecorators
class AccountBase(BaseModel):
    username: str
    password: str | None = None
    country: str = DEFAULT_COUNTRY

    @property
    def phone_number(self):
        return int(self.username[2:]) \
            if len(self.username) > PHONE_NUMBER_LENGTH \
            else int(self.username)

    @property
    def phone_prefix(self):
        return int(self.username[:2]) \
            if len(self.username) > PHONE_NUMBER_LENGTH \
            else PHONE_PREFIXES.get(self.country.lower())

    @field_validator('username', mode='before')
    @classmethod
    def validate_username(cls, v: str):
        return str(v).replace(' ', '')

    def get_query_params(self):
        """Get query params."""
        return {
            'retning': self.phone_prefix,
            'telefon': self.phone_number,
            'passord': self.password,
        }


class Account(AccountBase):
    uid: int | None
    auth_status: AuthStatus | None
    status: str | None


# noinspection PyNestedDecorators
class PoliceControlType(PolitiKontrollerResponse):
    id: int
    name: PoliceControlTypeEnum
    slug: str

    attr_map = [
        'slug',
        'name',
        'id',
        None,
    ]

    @field_validator('slug', mode='before')
    @classmethod
    def validate_slug(cls, v: str):
        # Remove ".png"
        return v[:-4]


class PoliceControlPoint:
    type: str = "Point"
    lat: float
    lng: float

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

    @property
    def coordinates(self):
        return self.lng, self.lat

    @property
    def __geo_interface__(self):
        return {
            'type': self.type,
            'coordinates': self.coordinates,
        }


# noinspection PyNestedDecorators
class PoliceControlResponse(PolitiKontrollerResponse):
    id: int
    county: str
    municipality: str
    type: PoliceControlTypeEnum
    timestamp: datetime | None
    description: str
    lat: float
    lng: float
    speed_limit: int | None = None
    last_seen: datetime | None
    confirmed: int = 0

    attr_map = [
        'id',  # 0  id: int  14241
        'county',  # 1  country: str       Trøndelag
        'municipality',  # 2  municipality: str   Malvik
        'type',  # 3  control_type: str   Fartskontroll
        'timestamp',  # 4     29.05 - 20:47
        'description',  # 5     Kontroll Olderdalen
        'lat',  # 6     63.4258007013951
        'lng',  # 7     10.6856604194473
        None,  # 8     |
        None,  # 9     |
        None,  # 10    malvik.png
        None,  # 11    trondelag.png
        'speed_limit',  # 12 speed_limit: int   90
        None,  # 13 enabled   1
        'last_seen',  # 14 last_seen: time   20:47
        'confirmed',  # 15 confirmed: str    0  (if not 0: confirmed=red)
        None,  # 16 confirmed   2   (0=green,  1=orange, 2=red)
        None,  # 17 control_type: int   1
    ]

    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v: int):
        return cls._timestamp_validate(v)

    @field_validator('last_seen', mode='before')
    @classmethod
    def validate_last_seen(cls, v: int):
        return cls._timestamp_validate(v)

    @property
    def description_truncated(self):
        return (
            self.description[:25] + '..'
        ) if len(self.description) > 27 else self.description  # noqa: PLR2004

    @property
    def title(self):
        return f"{self.type}: {self.description_truncated}"

    @classmethod
    def _timestamp_validate(cls, v: str | int) -> int | str | None:
        if len(v) == 0 or (v.isnumeric() and int(v) == 0):
            return None
        return parse_time_format(v)

    @property
    def _geometry(self):
        return PoliceControlPoint(self.lat, self.lng)

    @property
    def __geo_interface__(self):
        return {
            "type": "Feature",
            "geometry": self._geometry.__geo_interface__,
            "properties": {
                "title": self.title,
                "description": self.description,
                "type": self.type,
            },
        }


# noinspection PyNestedDecorators
class PoliceGPSControlsResponse(PolitiKontrollerResponse):
    id: int
    county: str
    municipality: str
    type: PoliceControlTypeEnum
    timestamp: datetime | None
    description: str
    lat: float
    lng: float

    attr_map = [
        'id',
        'county',
        'municipality',
        'type',
        'timestamp',
        'description',
        'lat',
        'lng',
        None,
        None,
        None,
        None,
    ]

    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v: int):
        return cls._timestamp_validate(v)

    @classmethod
    def _timestamp_validate(cls, v: str | int) -> int | str | None:
        if len(v) == 0 or (v.isnumeric() and int(v) == 0):
            return None
        return parse_time_format(v)


# noinspection PyNestedDecorators
class PoliceControlsResponse(PolitiKontrollerResponse):
    id: int
    county: str
    municipality: str
    type: PoliceControlTypeEnum
    timestamp: datetime | None
    description: str
    lat: float
    lng: float
    last_seen: datetime | None

    attr_map = [
        'id',
        'county',
        'municipality',
        'type',
        None,
        'description',
        'lat',
        'lng',
        None,
        None,
        None,
        None,
        'timestamp',
        None,
        None,
        'last_seen',
    ]

    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v: int):
        return cls._timestamp_validate(v)

    @field_validator('last_seen', mode='before')
    @classmethod
    def validate_last_seen(cls, v: int):
        return cls._timestamp_validate(v)

    @classmethod
    def _timestamp_validate(cls, v: str | int) -> int | str | None:
        if len(v) == 0 or (v.isnumeric() and int(v) == 0):
            return None
        return parse_time_format(v)


class UserMap(PolitiKontrollerResponse):
    id: int
    title: str
    country: str

    attr_map = [
        'id',
        None,
        'title',
        'country',
    ]


class ExchangePointsResponse(PolitiKontrollerResponse):
    status: ExchangeStatus
    message: str
