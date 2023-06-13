""" Handles requests and data untanglement towards retarded web service. """

from logging import getLogger
from .constants import (
    NO_CONTROLS,
    NO_ACCESS_RESPONSES
)
from .utils import (
    do_external_api_request,
    map_response_data,
)
from .models import (
    Account,
    AuthStatus,
)
from .exceptions import (
    NoAccessException,
    AuthenticationError,
)

_LOGGER = getLogger(__name__)


class Client:
    def __init__(self, user: Account | None = None):
        self.user = user

    def _api_request(self, params: dict, headers: dict | None = None):
        method = params.get('p')
        if method != 'l' and self.user:
            params = params | self.user.get_query_params()
        data = do_external_api_request(params, headers)
        if data in NO_ACCESS_RESPONSES:
            raise NoAccessException()
        _LOGGER.debug("Got response: %s", data)
        return data

    def set_user(self, user: Account):
        self.user = user

    def authenticate_user(self, username: str, password: str):
        auth_user = Account(**{"username": username, "password": password})
        params = {
            'p': 'l',
            'lang': 'no',
        } | auth_user.get_query_params()

        result = self._api_request(params)
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
            **user_dict
        } | auth_user.get_query_params()
        account = Account(**{str(k): str(v) for k, v in account_dict.items()})
        self.set_user(account)
        return account

    def get_settings(self):
        params = {
            'p': 'instillinger',
        }
        return self._api_request(params)

    def get_control(self, cid: int):
        params = {
            'p': 'hki',
            'kontroll_id': cid,
        }
        result = self._api_request(params)
        return map_response_data(result, [
            'id',            # 14241
            'county',        # Trøndelag
            'municipality',  # Malvik
            'type',          # Fartskontroll
            'timestamp',     # 29.05 - 20:47
            'description',   # Kontroll Olderdalen
            'lat',           # 63.4258007013951
            'lng',           # 10.6856604194473
            None,            # |
            None,            # |
            None,            # malvik.png
            None,            # trondelag.png
            'speed_limit',   # 90
            None,            # 1
            'last_seen',     # 20:47
            'confirmed',     # 0
            None,            # 2
            None,            # 1
        ])

    def get_controls(
        self,
        lat: float,
        lng: float,
        **kwargs,
    ):
        params = {
            'p': 'hk',
            **{
                'lat': lat,
                'lon': lng,
            },
            **kwargs,
        }

        result = self._api_request(params)
        if result == NO_CONTROLS:
            return []

        return map_response_data(result, [
            'id',           # 14239
            'county',       # Trøndelag
            'municipality', # Meråker
            'type',         # Toll/grense
            None,           # 20:02
            'description',  # Toll
            'lat',          # 63.3621679609569
            'lng',          # 11.9694197550416
            None,           # NOT_IN_USE
            None,           # meraaker.png
            None,           # YES
            None,           # meraaker.png
            'timestamp',    # 1685383334
            None,           # 0
            None,           # 20:04
            'last_seen',    # 1685383471
        ], multiple=True)

    def get_controls_in_radius(
        self,
        lat: float,
        lng: float,
        radius: int,
        speed: int = 100,
        **kwargs,
    ):
        return self.get_controls(lat, lng, p='gps_kontroller', vr=radius, speed=speed, **kwargs)

    def get_control_types(self):
        params = {
            'p': 'kontrolltyper',
        }
        result = self._api_request(params)

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

    def get_maps(self):
        params = {
            'p': 'hent_mine_kart',
        }
        result = self._api_request(params)
        data = map_response_data(result, [
            'id',
            None,
            'title',
            'country',
        ], multiple=True)
        return data

    def exchange_points(self):
        params = {
            'p': 'veksle',
        }
        result = self._api_request(params)
        data = map_response_data(result, [
            'status',
            'message',
        ])
        return data
