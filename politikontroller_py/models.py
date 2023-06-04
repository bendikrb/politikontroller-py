""" Politikontroller models """

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
    uid: int
    status: AuthStatus
    country: str
    phone_prefix: int
    phone_number: int
    password: str | None
    state: str

    @property
    def username(self):
        return f"{self.phone_prefix}{self.phone_number}"

    def get_query_params(self):
        """ Get query params. """
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
    """
     14242|Trøndelag|Trondheim|Observasjon  |21:04|Uniformert politibi|63.347522180959 |10.3714974432077|NOT_IN_USE|trondheim.png|YES|trondheim.png|1685387059|0|53 year|0
     14241|Trøndelag|Malvik   |Fartskontroll|20:47|Kontroll Olderdalen|63.4258007013951|10.6856604194473|NOT_IN_USE|malvik.png   |YES|malvik.png   |1685386077|0|53 year|0
     14239|Trøndelag|Meråker  |Toll/grense  |20:02|Toll               |63.3621679609569|11.9694197550416|NOT_IN_USE|meraaker.png |YES|meraaker.png |1685383334|0|20:04  |1685383471
     14243|Ullensaker|Ullensaker|Observasjon|21:08|Står i krysset     |60.1525910906892|11.1852279165936|          |             |Viken/Ullensaker - 21:08|5
    """
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

