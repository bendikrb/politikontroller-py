"""Handles requests and data un-entanglement to a truly retarded web service."""
from __future__ import annotations

import binascii
from logging import getLogger
from typing import TypeVar, cast
from urllib.parse import urlencode

import aiohttp

from .constants import (
    API_URL,
    CLIENT_TIMEOUT,
    CLIENT_VERSION_NUMBER,
    NO_ACCESS_RESPONSES,
    NO_CONTROLS,
)
from .exceptions import (
    AuthenticationError,
    NoAccessError,
)
from .models import (
    Account,
    AuthStatus,
    BaseResponseModel,
)
from .utils import (
    aes_decrypt,
    aes_encrypt,
    get_query_params,
    map_response_data,
)

ResponseT = TypeVar(
    "ResponseT",
    bound=str | BaseResponseModel | list[BaseResponseModel] | None,
)

JUNK_CHARS = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x10\x0f'

_LOGGER = getLogger(__name__)


class Client:
    def __init__(
        self,
        user: Account | None = None,
        session: aiohttp.ClientSession | None = None,
    ):
        self.user = user
        self._web_session = session

    @classmethod
    def initialize(cls, username: str, password: str) -> Client:
        return cls(Account(username=username, password=password))

    @classmethod
    def login(cls, username: str, password: str) -> Client:
        c = cls()
        c.authenticate_user(username, password)
        return c

    @property
    def web_session(self):
        if self._web_session:
            return self._web_session
        return aiohttp.ClientSession()

    async def api_request(
        self,
        params: dict,
        headers: dict | None = None,
        cast_to: type[ResponseT] | None = None,
    ) -> ResponseT:
        method = params.get('p')
        if method != 'l' and self.user:
            params.update(self.user.get_query_params())
        data = await self.do_external_api_request(params, headers)
        if data in NO_ACCESS_RESPONSES:
            raise NoAccessError
        _LOGGER.debug("Got response: %s", data)
        if cast_to is not None:
            if isinstance(data, list):
                return [cast(cast_to, cast_to.parse_obj(d)) for d in data]
            return cast(cast_to, cast_to.parse_obj(data))
        return data

    async def do_external_api_request(
        self,
        params: dict,
        headers: dict | None = None
    ):
        if headers is None:
            headers = {}

        payload = get_query_params(params)
        _LOGGER.debug("Doing API request with params: %s", payload)
        url = f'{API_URL}/app.php?{aes_encrypt(urlencode(payload))}'
        headers = {
            'user-agent': f'PK_{CLIENT_VERSION_NUMBER}',
            **headers,
        }

        async with self.web_session as session:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=CLIENT_TIMEOUT),
            ) as resp:
                enc_data = await resp.text('utf-8')
                try:
                    data = aes_decrypt(enc_data)
                except binascii.Error:
                    data = enc_data

                return data.strip(JUNK_CHARS).strip()

    def set_user(self, user: Account):
        self.user = user

    async def authenticate_user(self, username: str, password: str):
        auth_user = Account(username=username, password=password)
        params = {
            'p': 'l',
            'lang': 'no',
            **auth_user.get_query_params(),
        }

        result = await self.api_request(params)
        _LOGGER.debug("Got result: %s", result)
        user_dict = map_response_data(result, [
            'status',
            'country',
            None,
            'phone_prefix',
            'state',
            'uid',
        ])
        if user_dict.get('status') == AuthStatus.LOGIN_ERROR:
            raise AuthenticationError

        account_dict = {
            **auth_user.dict(),
            **user_dict,
            **{"username": f"{user_dict['phone_prefix']}{auth_user.username}"}  # noqa: PIE800
        }

        account = Account(**{str(k): str(v) for k, v in account_dict.items()})
        self.set_user(account)
        return account

    async def get_settings(self):
        params = {
            'p': 'instillinger',
        }
        return await self.api_request(params)

    async def get_control(self, cid: int):
        params = {
            'p': 'hki',
            'kontroll_id': cid,
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'id',  # 14241
            'county',  # Trøndelag
            'municipality',  # Malvik
            'type',  # Fartskontroll
            'timestamp',  # 29.05 - 20:47
            'description',  # Kontroll Olderdalen
            'lat',  # 63.4258007013951
            'lng',  # 10.6856604194473
            None,  # |
            None,  # |
            None,  # malvik.png
            None,  # trondelag.png
            'speed_limit',  # 90
            None,  # 1
            'last_seen',  # 20:47
            'confirmed',  # 0
            None,  # 2
            None,  # 1
        ])

    async def get_controls(
        self,
        lat: float,
        lng: float,
        **kwargs,
    ):
        params = {
            'p': 'hk',
            'lat': lat,
            'lon': lng,
            **kwargs,
        }

        result = await self.api_request(params)
        if result == NO_CONTROLS:
            return []

        return map_response_data(result, [
            'id',  # 14239
            'county',  # Trøndelag
            'municipality',  # Meråker
            'type',  # Toll/grense
            None,  # 20:02
            'description',  # Toll
            'lat',  # 63.3621679609569
            'lng',  # 11.9694197550416
            None,  # NOT_IN_USE
            None,  # meraaker.png
            None,  # YES
            None,  # meraaker.png
            'timestamp',  # 1685383334
            None,  # 0
            None,  # 20:04
            'last_seen',  # 1685383471
        ], multiple=True)

    async def get_controls_in_radius(
        self,
        lat: float,
        lng: float,
        radius: int,
        speed: int = 100,
        **kwargs,
    ):

        params = {
            'p': 'gps_kontroller',
            'vr': radius,
            'speed': speed,
            'lat': lat,
            'lon': lng,
            **kwargs,
        }

        result = await self.api_request(params)
        if result == NO_CONTROLS:
            return []

        return map_response_data(result, [
            'id',           # 30288
            'county',       # Strand
            'municipality', # Strand
            'type',         # Teknisk
            'timestamp',    # 10:12
            'description',  # Ved Strand VGs
            'lat',          # 59.0633822267745
            'lng',          # 5.92275018667227
            None,           #
            None,           #
            None,           # Rogaland / Strand - 10:12
            None,           # 3
        ], multiple=True)

    async def get_control_types(self):
        params = {
            'p': 'kontrolltyper',
        }
        result = await self.api_request(params)

        data = map_response_data(result, [
            'slug',
            'name',
            'id',
            None,
        ], multiple=True)
        return [
            {
                # Remove ".png"
                key: val[:-4] if key == 'slug' else val
                for key, val in el.items()
            }
            for el in data
        ]

    async def get_maps(self):
        params = {
            'p': 'hent_mine_kart',
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'id',
            None,
            'title',
            'country',
        ], multiple=True)

    async def exchange_points(self):
        params = {
            'p': 'veksle',
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'status',
            'message',
        ])
