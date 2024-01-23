"""Handles requests and data un-entanglement to a truly retarded web service."""
from __future__ import annotations

import binascii
import logging
from typing import TypeVar, cast
from urllib.parse import urlencode

import aiohttp

from .constants import (
    API_URL,
    CLIENT_TIMEOUT,
    CLIENT_VERSION_NUMBER,
    DEFAULT_COUNTRY,
    NO_ACCESS_RESPONSES,
    NO_CONTENT_RESPONSES,
    PHONE_PREFIXES,
)
from .exceptions import (
    AuthenticationBlockedError,
    AuthenticationError,
    NoAccessError,
    NoContentError,
    NotActivatedError,
)
from .models import (
    Account,
    AccountBase,
    AuthenticationResponse,
    AuthStatus,
    PoliceControlResponse,
    PoliceControlsResponse,
    PoliceControlType,
    PoliceGPSControlsResponse,
    PolitiKontrollerResponse,
    UserMap,
)
from .utils import (
    aes_decrypt,
    aes_encrypt,
    get_query_params,
    map_response_data,
)

ResponseT = TypeVar(
    "ResponseT",
    bound=PolitiKontrollerResponse | dict[str, any],
)

JUNK_CHARS = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x10\x0f'

_LOGGER = logging.getLogger(__name__)


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
    async def login(cls, username: str, password: str) -> Client:
        c = cls()
        await c.authenticate_user(username, password)
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
        is_list=False,
    ) -> ResponseT | list[ResponseT] | str:
        method = params.get('p')
        no_auth_methods = ['l', 'r', 'check', 'endre_passord', 'endrings_kode']
        if method not in no_auth_methods and self.user:
            params.update(self.user.get_query_params())
        data = await self.do_external_api_request(params, headers)
        _LOGGER.debug("Got response: %s", data)
        if data in NO_ACCESS_RESPONSES:
            raise NoAccessError
        if data in NO_CONTENT_RESPONSES:
            raise NoContentError

        # Attempt to cast the response data to desired model
        if cast_to is not None:
            model_data = cast_to.from_response_data(data, multiple=is_list)
            if is_list:
                return [cast(cast_to, cast_to.model_validate(d)) for d in model_data]
            return cast(cast_to, cast_to.model_validate(model_data))

        # Return the raw response (str)
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
        auth_user = AccountBase(username=username, password=password)
        params = {
            'p': 'l',
            'lang': auth_user.country.lower(),
            **auth_user.get_query_params(),
        }

        result = await self.api_request(params, cast_to=AuthenticationResponse)
        _LOGGER.debug("Got result: %s", result)

        if result.auth_status == AuthStatus.LOGIN_ERROR:
            raise AuthenticationError
        if result.auth_status == AuthStatus.SPERRET:
            raise AuthenticationBlockedError
        if result.auth_status == AuthStatus.NOT_ACTIVATED:
            raise NotActivatedError

        account_dict = {
            **auth_user.model_dump(),
            **result.model_dump(),
            **{"username": f"{auth_user.username}"},  # noqa: PIE800
        }

        account = Account(**{str(k): str(v) for k, v in account_dict.items()})
        self.set_user(account)
        return account

    async def get_settings(self):
        params = {
            'p': 'instillinger',
        }
        return await self.api_request(params)

    async def get_control(self, cid: int) -> PoliceControlResponse:
        params = {
            'p': 'hki',
            'kontroll_id': cid,
        }
        return await self.api_request(params, cast_to=PoliceControlResponse)

    async def get_controls(
        self,
        lat: float,
        lng: float,
        **kwargs,
    ) -> list[PoliceControlsResponse]:
        params = {
            'p': 'hk',
            'lat': lat,
            'lon': lng,
            **kwargs,
        }

        try:
            return await self.api_request(
                params,
                cast_to=PoliceControlsResponse,
                is_list=True,
            )
        except NoContentError:
            return []

    async def get_controls_in_radius(
        self,
        lat: float,
        lng: float,
        radius: int,
        speed: int = 100,
        **kwargs,
    ) -> list[PoliceGPSControlsResponse]:
        params = {
            'p': 'gps_kontroller',
            'vr': radius,
            'speed': speed,
            'lat': lat,
            'lon': lng,
            **kwargs,
        }

        try:
            return await self.api_request(
                params,
                cast_to=PoliceGPSControlsResponse,
                is_list=True,
            )
        except NoContentError:
            return []

    async def get_controls_from_lists(
        self,
        controls: list[PoliceGPSControlsResponse | PoliceControlsResponse],
    ) -> list[PoliceControlResponse]:
        return [await self.get_control(i.id) for i in controls]

    async def get_control_types(self) -> list[PoliceControlType]:
        params = {
            'p': 'kontrolltyper',
        }
        return await self.api_request(params, cast_to=PoliceControlType, is_list=True)

    async def get_maps(self) -> list[UserMap]:
        params = {
            'p': 'hent_mine_kart',
        }
        return await self.api_request(params, cast_to=UserMap, is_list=True)

    async def exchange_points(self):
        params = {
            'p': 'veksle',
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'status',
            'message',
        ])

    async def account_register(
        self,
        phone_number: int,
        password: str,
        name: str,
        country: str | None = None,
    ):
        if country is None:
            country = DEFAULT_COUNTRY
        country_code = PHONE_PREFIXES.get(country, 00)

        params = {
            'p': 'r',
            'telefon': phone_number,
            'passord': password,
            'cc': country_code,
            'navn': name,
            'lang': country,
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'status',
            'message',
        ])

    async def account_auth(self, auth_code: str, uid: int):
        params = {
            'p': 'auth_app',
            'auth_kode': auth_code,
            'uid': uid,
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'status',
            'message',
        ])

    async def account_auth_sms(self):
        params = {
            'p': 'auth_sms',
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'status',
            'message',
        ])

    async def account_send_sms(self):
        params = {
            'p': 'send_sms',
        }
        result = await self.api_request(params)
        return map_response_data(result, [
            'status',
            'message',
        ])
