"""Handles requests and data un-entanglement to a truly retarded web service."""

from __future__ import annotations

import asyncio
import binascii
from dataclasses import dataclass
from http import HTTPStatus
import logging
from typing import TypeVar, cast
from urllib.parse import urlencode

from aiohttp import ClientError, ClientResponse, ClientResponseError, ClientSession
import async_timeout

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
    NotFoundError,
    PolitikontrollerConnectionError,
    PolitikontrollerError,
    PolitikontrollerTimeoutError,
)
from .models import (
    Account,
    AuthenticationResponse,
    AuthStatus,
    PoliceControlResponse,
    PoliceControlsResponse,
    PoliceControlType,
    PoliceGPSControlsResponse,
    PolitiKontrollerResponse,
    UserMap,
)
from .models.api import APIEndpoint, EndpointRegistry, PolitiKontrollerRequest
from .utils import (
    aes_decrypt,
    aes_encrypt,
    map_response_data,
)

ResponseT = TypeVar(
    "ResponseT",
    bound=PolitiKontrollerResponse | dict[str, any],
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class Client:
    user: Account | None = None
    session: ClientSession | None = None
    request_timeout: int = CLIENT_TIMEOUT

    _close_session: bool = False

    @classmethod
    def initialize(cls, username: str, password: str) -> Client:
        return cls(Account(username=username, password=password))

    @classmethod
    async def login(cls, username: str, password: str) -> Client:
        c = cls()
        await c.authenticate_user(username, password)
        return c

    @property
    def request_header(self) -> dict[str, str]:
        """Generate a header for HTTP requests to the server."""
        return {
            "User-Agent": f"PK_{CLIENT_VERSION_NUMBER}",
        }

    async def api_request(
        self,
        endpoint: APIEndpoint | str,
        params: dict | None = None,
        cast_to: type[ResponseT] | None = None,
        is_list=False,
    ) -> ResponseT | list[ResponseT] | str:
        if params is None:
            params = {}
        if isinstance(endpoint, str):
            endpoint = APIEndpoint.from_str(endpoint)

        # Build request
        request_cls = EndpointRegistry.get_request_class(endpoint)
        if endpoint.requires_auth():
            if self.user is None:
                raise AuthenticationError("Trying to access authenticated API without authentication")
            params["account"] = self.user.to_dict()
        params["p"] = endpoint
        request = request_cls.from_dict(params)

        data = await self.do_external_api_request(request)
        data_parts = data.split("|")
        _LOGGER.debug("Got response: %s", data)

        if data in NO_ACCESS_RESPONSES:
            raise NoAccessError
        if data in NO_CONTENT_RESPONSES:
            raise NoContentError
        if data_parts[0] in NO_CONTENT_RESPONSES:
            raise NoContentError
        if data_parts[0] == AuthStatus.LOGIN_ERROR:
            msg = f"Authentication failed: {data_parts[1]}"
            raise AuthenticationError(msg)

        # Attempt to cast the response data to desired model
        if cast_to is not None:
            model_data = cast_to.from_response_data(data, multiple=is_list)
            if is_list:
                return [cast(cast_to, cast_to.from_dict(d)) for d in model_data]
            return cast(cast_to, cast_to.from_dict(model_data))

        # Return the raw response (str)
        return data

    def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = ClientSession()
            _LOGGER.debug("New session created.")
            self._close_session = True

    @staticmethod
    async def _request_check_status(response: ClientResponse):
        if response.status == HTTPStatus.NOT_FOUND:
            raise NotFoundError("Resource not found")
        if response.status == HTTPStatus.BAD_REQUEST:
            raise PolitikontrollerError("Bad request syntax or unsupported method")
        if response.status == HTTPStatus.FORBIDDEN:
            raise AuthenticationError("Authorization failed")
        if not HTTPStatus(response.status).is_success:
            raise PolitikontrollerError(response)

    async def do_external_api_request(
        self,
        request: PolitiKontrollerRequest,
        **kwargs,
    ) -> str:
        headers = kwargs.get("headers")
        headers = self.request_header if headers is None else dict(headers)

        payload = request.get_query_params()
        _LOGGER.debug("Doing API request with params: %s", payload)
        url = f"{API_URL}/app.php?{aes_encrypt(urlencode(payload))}"
        headers = {
            "user-agent": f"PK_{CLIENT_VERSION_NUMBER}",
            **headers,
        }

        self._ensure_session()

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.get(
                    url,
                    **kwargs,
                    headers=headers,
                    raise_for_status=self._request_check_status,
                )
                enc_data = await response.text("utf-8")
                try:
                    data = aes_decrypt(enc_data)
                except binascii.Error:
                    data = enc_data

                return data

        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Politikontroller.no"
            raise PolitikontrollerTimeoutError(msg) from exception
        except (
            ClientError,
            ClientResponseError,
        ) as exception:
            raise PolitikontrollerConnectionError(
                f"Error occurred while communicating with Politikontroller.no: {exception}",
            ) from exception
        finally:
            if self._close_session:
                await self.session.close()
                self._close_session = False

    def set_user(self, user: Account):
        self.user = user

    async def authenticate_user(self, username: str, password: str) -> Account:
        """Authenticate user."""
        auth_user = Account(username=username, password=password)
        params = {
            "lang": auth_user.country.lower(),
            "account": auth_user.to_dict(),
        }

        result = await self.api_request(APIEndpoint.LOGIN, params, cast_to=AuthenticationResponse)
        if result.auth_status == AuthStatus.LOGIN_ERROR:
            msg = f"Authentication failed: {result.auth_status}"
            raise AuthenticationError(msg)
        if result.auth_status == AuthStatus.SPERRET:
            raise AuthenticationBlockedError
        if result.auth_status == AuthStatus.NOT_ACTIVATED:
            raise NotActivatedError

        account_dict = {
            **auth_user.to_dict(),
            **result.to_dict(),
            "username": auth_user.username,
        }

        account = Account.from_dict({str(k): str(v) for k, v in account_dict.items()})
        self.set_user(account)
        return account

    async def check(self):
        """Server health check."""
        return await self.api_request(APIEndpoint.CHECK)

    async def get_settings(self):
        """Get settings."""
        return await self.api_request(APIEndpoint.SETTINGS)

    async def get_control(self, cid: int) -> PoliceControlResponse:
        """Get details for a single control."""
        return await self.api_request(
            APIEndpoint.SPEED_CONTROL,
            {
                "kontroll_id": cid,
            },
            cast_to=PoliceControlResponse,
        )

    async def get_controls(
        self,
        lat: float,
        lng: float,
    ) -> list[PoliceControlsResponse]:
        """Get all active controls."""
        try:
            return await self.api_request(
                APIEndpoint.SPEED_CONTROLS,
                {
                    "lat": lat,
                    "lon": lng,
                },
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
        """Get all active controls within a radius."""
        params = {
            "vr": radius,
            "speed": speed,
            "lat": lat,
            "lon": lng,
            **kwargs,
        }
        try:
            return await self.api_request(
                APIEndpoint.GPS_CONTROLS,
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
        """Get details for a list of controls."""
        return [await self.get_control(i.id) for i in controls]

    async def get_control_types(self) -> list[PoliceControlType]:
        """Get all control types."""
        return await self.api_request(
            APIEndpoint.CONTROL_TYPES,
            cast_to=PoliceControlType,
            is_list=True,
        )

    async def get_maps(self) -> list[UserMap]:
        """Get all user maps."""
        return await self.api_request(APIEndpoint.GET_MY_MAPS, cast_to=UserMap, is_list=True)

    async def exchange_points(self):
        """Exchange points."""
        result = await self.api_request(APIEndpoint.EXCHANGE)
        return map_response_data(
            result,
            [
                "status",
                "message",
            ],
        )

    async def account_register(
        self,
        phone_number: int,
        password: str,
        name: str,
        country: str | None = None,
    ):
        if country is None:
            country = DEFAULT_COUNTRY
        country_code = PHONE_PREFIXES.get(country)

        params = {
            "telefon": phone_number,
            "passord": password,
            "cc": country_code,
            "navn": name,
            "lang": country,
        }
        result = await self.api_request(APIEndpoint.REGISTER, params)
        return map_response_data(
            result,
            [
                "status",
                "message",
            ],
        )

    async def account_auth(self, auth_code: str, uid: int):
        """Activate account by auth code."""
        params = {
            "auth_kode": auth_code,
            "uid": uid,
        }
        result = await self.api_request(APIEndpoint.AUTH_APP, params)
        return map_response_data(
            result,
            [
                "status",
                "message",
            ],
        )

    async def account_auth_sms(self):
        """Activate account by sms."""
        result = await self.api_request(APIEndpoint.AUTH_SMS)
        return map_response_data(
            result,
            [
                "status",
                "message",
            ],
        )

    async def account_send_sms(self):
        """Send activation sms."""
        result = await self.api_request(APIEndpoint.SEND_SMS)
        return map_response_data(
            result,
            [
                "status",
                "message",
            ],
        )
