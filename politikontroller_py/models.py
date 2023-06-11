""" Politikontroller models """

import re
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, validator

from .utils import parse_time_format


class AuthStatus(str, Enum):
    LOGIN_OK = 'LOGIN_OK'
    LOGIN_ERROR = 'LOGIN_ERROR'


class ExchangeStatus(str, Enum):
    EXCHANGE_OK = 'EXCHANGE_OK'


class PoliceControlTypeEnum(str, Enum):
    SPEED_TRAP = "Fartskontroll"
    BEHAVIOUR = "Belte/mobil"
    TECHNICAL = "Teknisk"
    TRAFFIC_INFO = "Trafikk info"
    OBSERVATION = "Observasjon"
    CUSTOMS = "Toll/grense"
    WEIGHT = "Vektkontroll"
    UNKNOWN = "Ukjent"
    CIVIL_POLICE = "Sivilpoliti"
    MC_CONTROL = "Mopedkontroll"
    BOAT_PATROL = "Politibåten"


class Account(BaseModel):
    uid: int | None
    status: AuthStatus | None
    country: str = "no"
    phone_prefix: int = 47
    phone_number: int
    password: str | None
    state: str | None

    @property
    def username(self):
        return f"{self.phone_prefix}{self.phone_number}"

    def set_username(self, value):
        clean_value = re.sub('\D', '', str(value))
        if len(clean_value) < 8:
            self.phone_number = int(clean_value)
        else:
            self.phone_prefix = int(clean_value[:2])
            self.phone_number = int(clean_value[2:])

    def __setattr__(self, key, val):
        method = self.__config__.property_set_methods.get(key)
        if method is None:
            super().__setattr__(key, val)
        else:
            getattr(self, method)(val)

    def get_query_params(self):
        """ Get query params. """
        return {
            'retning': self.phone_prefix,
            'telefon': self.phone_number,
            'passord': self.password,
        }

    class Config:
        property_set_methods = {"username": "set_username"}


class PoliceControlType(BaseModel):
    id: int
    name: PoliceControlTypeEnum
    slug: str


class PoliceControlPoint:
    lat: float
    lng: float

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

    @property
    def __geo_interface__(self):
        return {
            'type': 'Point',
            'coordinates': (self.lat, self.lng),
        }


class PoliceControl(BaseModel):
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
    def timestamp_validate(cls, v):
        if len(v) == 0 or (v.isnumeric() and int(v) == 0):
            return None
        return parse_time_format(v)

    @validator('last_seen', pre=True)
    def last_seen_validate(cls, v):
        if len(v) == 0 or (v.isnumeric() and int(v) == 0):
            return None
        return parse_time_format(v)

    @property
    def description_truncated(self):
        return (
            self.description[:25] + '..'
        ) if len(self.description) > 27 else self.description

    @property
    def title(self):
        return f"{self.type.value}: {self.description_truncated}"

    @property
    def _geometry(self):
        return PoliceControlPoint(self.lat, self.lng)

    @property
    def __geo_interface__(self):
        return {
            "type": "Feature",
            "geometry": self._geometry,
            "properties": {
                "title": self.title,
                "description": self.description,
                "type": self.type,
            },
        }


class ExchangePointsResponse(BaseModel):
    status: ExchangeStatus
    message: str

