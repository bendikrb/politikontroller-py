from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import TYPE_CHECKING, ClassVar, Literal, TypeVar

from mashumaro import field_options
from mashumaro.config import BaseConfig

from politikontroller_py.constants import (
    CLIENT_OS,
    CLIENT_VERSION_NUMBER,
    DESCRIPTION_TRUNCATE_LENGTH,
    DESCRIPTION_TRUNCATE_SUFFIX,
)
from politikontroller_py.models.account import Account  # noqa: TCH001
from politikontroller_py.models.common import (
    BaseModel,
    PolitiKontrollerResponse,
    StrEnum,
)
from politikontroller_py.utils import get_random_string, get_unix_timestamp, parse_datetime_like

if TYPE_CHECKING:
    from politikontroller_py.models.common import T


# noinspection SpellCheckingInspection
class PoliceControlTypeEnum(StrEnum):
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


class ExchangeStatus(StrEnum):
    EXCHANGE_OK = "EXCHANGE_OK"


class PoliceControlType(PolitiKontrollerResponse):
    id: int
    name: PoliceControlTypeEnum
    slug: str

    attr_map = [
        "slug",
        "name",
        "id",
        None,
    ]

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        # Remove ".png"
        d["slug"] = d.get("slug", "")[:-4]
        return d


@dataclass
class PoliceControlPoint(BaseModel):
    lat: float
    lng: float
    type: str = "Point"

    @property
    def coordinates(self):
        return self.lng, self.lat

    @property
    def __geo_interface__(self):
        return {
            "type": self.type,
            "coordinates": self.coordinates,
        }


# noinspection SpellCheckingInspection
@dataclass(kw_only=True)
class PoliceControlResponse(PolitiKontrollerResponse):
    id: int
    county: str
    municipality: str
    type: PoliceControlTypeEnum
    timestamp: datetime | None = field(
        default=None,
        metadata=field_options(
            deserialize=datetime.fromtimestamp,
            serialize=lambda v: int(datetime.timestamp(v)),
        ),
    )
    description: str
    lat: float
    lng: float
    speed_limit: int | None = None
    last_seen: datetime | None = field(
        default=None,
        metadata=field_options(
            deserialize=datetime.fromtimestamp,
            serialize=lambda v: int(datetime.timestamp(v)),
        ),
    )
    confirmed: int = 0

    attr_map = [
        "id",  # 0  id: int  14241
        "county",  # 1  country: str       Trøndelag
        "municipality",  # 2  municipality: str   Malvik
        "type",  # 3  control_type: str   Fartskontroll
        "timestamp",  # 4     29.05 - 20:47
        "description",  # 5     Kontroll Olderdalen
        "lat",  # 6     63.4258007013951
        "lng",  # 7     10.6856604194473
        None,  # 8     |
        None,  # 9     |
        None,  # 10    malvik.png
        None,  # 11    trondelag.png
        "speed_limit",  # 12 speed_limit: int   90
        None,  # 13 enabled   1
        "last_seen",  # 14 last_seen: time   20:47
        "confirmed",  # 15 confirmed: str    0  (if not 0: confirmed=red)
        None,  # 16 confirmed   2   (0=green,  1=orange, 2=red)
        None,  # 17 control_type: int   1
    ]

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        for k in ["timestamp", "last_seen"]:
            d[k] = parse_datetime_like(d.get(k, ""))
        return d

    @property
    def description_truncated(self):
        trunc_len = DESCRIPTION_TRUNCATE_LENGTH - len(DESCRIPTION_TRUNCATE_SUFFIX)
        return (
            f"{self.description[:trunc_len]}{DESCRIPTION_TRUNCATE_SUFFIX}"
            if len(self.description) > DESCRIPTION_TRUNCATE_LENGTH
            else self.description
        )

    @property
    def title(self):
        return f"{self.type}: {self.description_truncated}"

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


@dataclass(kw_only=True)
class PoliceGPSControlsResponse(PolitiKontrollerResponse):
    id: int
    county: str
    municipality: str
    type: PoliceControlTypeEnum
    timestamp: datetime | None = field(
        default=None,
        metadata=field_options(
            deserialize=datetime.fromtimestamp,
            serialize=lambda v: int(datetime.timestamp(v)),
        ),
    )
    description: str
    lat: float
    lng: float

    attr_map = [
        "id",
        "county",
        "municipality",
        "type",
        "timestamp",
        "description",
        "lat",
        "lng",
        None,
        None,
        None,
        None,
    ]

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        for k in ["timestamp"]:
            d[k] = parse_datetime_like(d.get(k, ""))
        return d


@dataclass(kw_only=True)
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
        "id",
        "county",
        "municipality",
        "type",
        None,
        "description",
        "lat",
        "lng",
        None,
        None,
        None,
        None,
        "timestamp",
        None,
        None,
        "last_seen",
    ]

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        for k in ["timestamp", "last_seen"]:
            d[k] = parse_datetime_like(d.get(k, ""))
        return d


@dataclass
class UserMap(PolitiKontrollerResponse):
    id: int
    title: str
    country: str

    attr_map = [
        "id",
        None,
        "title",
        "country",
    ]


@dataclass
class ExchangePointsResponse(PolitiKontrollerResponse):
    status: ExchangeStatus
    message: str


TR = TypeVar("TR", bound="PolitiKontrollerRequest")


class EndpointRegistry:
    _registry: dict[APIEndpoint, type[PolitiKontrollerRequest]] = {}

    @classmethod
    def register(cls, endpoint: APIEndpoint) -> callable:
        def decorator(request_class: type[TR]) -> type[TR]:
            request_class.p = endpoint.value
            cls._registry[endpoint] = request_class
            return request_class

        return decorator

    @classmethod
    def get_request_class(cls, endpoint: APIEndpoint) -> type[PolitiKontrollerRequest]:
        if endpoint not in cls._registry:
            raise ValueError(f"No request class mapped for endpoint {endpoint}")
        return cls._registry[endpoint]


# noinspection SpellCheckingInspection
class APIEndpoint(StrEnum):
    AUTH_APP = "auth_app"
    AUTH_SMS = "auth_sms"
    CHANGE_PASSWORD = "endre_passord"
    CHANGE_PASSWORD_CODE = "endrings_kode"
    CHECK = "check"
    CONTROL_TYPES = "kontrolltyper"
    EXCHANGE = "veksle"
    GET_MY_MAPS = "hent_mine_kart"
    GPS_CONTROLS = "gps_kontroller"
    LOGIN = "l"
    REGISTER = "r"
    SEND_SMS = "send_sms"
    SETTINGS = "instillinger"
    SPEED_CONTROL = "hki"
    SPEED_CONTROLS = "hk"

    def requires_auth(self) -> bool:
        no_auth_methods = [
            APIEndpoint.LOGIN,
            APIEndpoint.REGISTER,
            APIEndpoint.CHANGE_PASSWORD,
            APIEndpoint.CHANGE_PASSWORD_CODE,
        ]
        return self not in no_auth_methods


API_ENDPOINTS = Literal[
    APIEndpoint.AUTH_APP,
    APIEndpoint.AUTH_SMS,
    APIEndpoint.CHANGE_PASSWORD,
    APIEndpoint.CHANGE_PASSWORD_CODE,
    APIEndpoint.CHECK,
    APIEndpoint.CONTROL_TYPES,
    APIEndpoint.EXCHANGE,
    APIEndpoint.GET_MY_MAPS,
    APIEndpoint.GPS_CONTROLS,
    APIEndpoint.LOGIN,
    APIEndpoint.REGISTER,
    APIEndpoint.SEND_SMS,
    APIEndpoint.SETTINGS,
    APIEndpoint.SPEED_CONTROL,
    APIEndpoint.SPEED_CONTROLS,
]


@dataclass
class PolitiKontrollerRequestBase(BaseModel):
    class Config(BaseConfig):
        omit_none = True
        allow_deserialization_not_by_alias = True
        serialize_by_alias = True


@dataclass
class PolitiKontrollerRequest(PolitiKontrollerRequestBase):
    p: APIEndpoint
    bac: str = field(default_factory=lambda: get_random_string(10))
    z: str = field(default_factory=lambda: str(get_unix_timestamp()))
    version: str = CLIENT_VERSION_NUMBER
    os: str = CLIENT_OS
    tt: str = field(default_factory=lambda: get_random_string(5))

    BASE_FIELDS: ClassVar[list[str]] = ["bac", "z", "version", "os", "tt"]

    def __post_serialize__(self, d: dict[str, any]) -> dict[str, any]:
        """Replace special characters in the base fields with hyphens."""
        for f in self.BASE_FIELDS:
            if f in d:
                d[f] = re.sub(r"[|#\\\"]", "-", str(d[f]))
        return d

    def requires_auth(self) -> bool:
        return self.p.requires_auth()

    def get_query_params(self) -> dict[str, str]:
        """Get query parameters in specific order.

        1. bac, z, version, os
        2. All other fields from to_dict()
        3. tt at the end
        """
        all_params = self.to_dict()
        query = OrderedDict()

        # Add first 4 params in order
        for param in self.BASE_FIELDS[:-1]:
            if param in all_params:
                query[param] = all_params[param]

        # Add all remaining params except sanitized fields
        for key, value in all_params.items():
            if key not in self.BASE_FIELDS:
                query[key] = value

        query["tt"] = all_params["tt"]

        return dict(query)


@dataclass
class PolitikontrollerAuthenticatedRequest(PolitiKontrollerRequestBase):
    retning: str = field(init=False)
    telefon: str = field(init=False)
    passord: str = field(init=False)
    account: Account = field(metadata=field_options(serialize="omit"))

    def __post_init__(self):
        self.retning = self.account.phone_prefix
        self.telefon = self.account.phone_number
        self.passord = self.account.password


@EndpointRegistry.register(APIEndpoint.LOGIN)
@dataclass(kw_only=True)
class PolitiKontrollerLoginRequest(PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest):
    lang: str


@EndpointRegistry.register(APIEndpoint.SPEED_CONTROLS)
@dataclass(kw_only=True)
class PolitiKontrollerGetControlsRequest(PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest):
    lat: float
    lon: float


@EndpointRegistry.register(APIEndpoint.GPS_CONTROLS)
@dataclass(kw_only=True)
class PolitiKontrollerGetControlsInRadiusRequest(
    PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest
):
    vr: int
    lat: float
    lon: float
    speed: int | None = None


@EndpointRegistry.register(APIEndpoint.SPEED_CONTROL)
@dataclass(kw_only=True)
class PolitiKontrollerGetControlRequest(PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest):
    kontroll_id: int


@EndpointRegistry.register(APIEndpoint.SETTINGS)
@dataclass
class PolitiKontrollerSettingsRequest(PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest):
    pass


@EndpointRegistry.register(APIEndpoint.GET_MY_MAPS)
@dataclass
class PolitiKontrollerGetMapsRequest(PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest):
    pass


@dataclass
class PolitiKontrollerGetControlTypesRequest(PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest):
    pass


@EndpointRegistry.register(APIEndpoint.CHECK)
@dataclass
class PolitiKontrollerCheckRequest(PolitiKontrollerRequest, PolitikontrollerAuthenticatedRequest):
    pass


@EndpointRegistry.register(APIEndpoint.REGISTER)
@dataclass(kw_only=True)
class PolitiKontrollerRegisterRequest(PolitiKontrollerRequest):
    telefon: str
    passord: str
    cc: str
    navn: str
    lang: str


@EndpointRegistry.register(APIEndpoint.AUTH_APP)
@dataclass(kw_only=True)
class PolitiKontrollerAuthAppRequest(PolitiKontrollerRequest):
    auth_kode: str
    uid: int
