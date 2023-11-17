"""Politikontroller models."""
from __future__ import annotations

from enum import Enum, StrEnum, auto

from pydantic import BaseModel, validator

from .constants import DEFAULT_COUNTRY, PHONE_NUMBER_LENGTH, PHONE_PREFIXES
from .utils import parse_time_format

from datetime import datetime


class AuthStatus(StrEnum):
    LOGIN_OK = auto()
    LOGIN_ERROR = auto()

    @classmethod
    def _missing_(cls, value: str) -> str | None:
        value = value.lower()
        for member in cls:
            if member == value:
                return member
        return None


class ExchangeStatus(StrEnum):
    EXCHANGE_OK = auto()


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


class Account(BaseResponseModel):
    uid: int | None
    status: AuthStatus | None
    country: str = DEFAULT_COUNTRY
    username: str
    password: str | None
    state: str | None

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

    @validator('username', pre=True)
    def validate_username(cls, v):  # noqa: N805
        return str(v).replace(' ', '')

    def get_query_params(self):
        """Get query params."""
        return {
            'retning': self.phone_prefix,
            'telefon': self.phone_number,
            'passord': self.password,
        }


class PoliceControlType(BaseModel):
    id: int
    name: PoliceControlTypeEnum
    slug: str


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


class PoliceControl(BaseResponseModel):
    id: int
    type: PoliceControlTypeEnum
    county: str
    speed_limit: int | None = None
    municipality: str
    description: str
    lat: float
    lng: float
    timestamp: datetime | None
    last_seen: datetime | None
    confirmed: int = 0

    @validator('timestamp', pre=True)
    def timestamp_validate(cls, v):  # noqa: N805
        return cls._timestamp_validate(v)

    @validator('last_seen', pre=True)
    def last_seen_validate(cls, v):  # noqa: N805
        return cls._timestamp_validate(v)

    @property
    def description_truncated(self):
        return (
            self.description[:25] + '..'
        ) if len(self.description) > 27 else self.description  # noqa: PLR2004

    @property
    def title(self):
        return f"{self.type.value}: {self.description_truncated}"

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


class ExchangePointsResponse(BaseResponseModel):
    status: ExchangeStatus
    message: str


PoliceControl.update_forward_refs()
