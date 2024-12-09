"""Tests for NrkPodcastAPI."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiohttp import ClientResponse, ClientSession
from aresponses import Response
import pytest

from politikontroller_py import Account, Client
from politikontroller_py.exceptions import (
    AuthenticationError,
    NotFoundError,
    PolitikontrollerConnectionError,
    PolitikontrollerError,
    PolitikontrollerTimeoutError,
)
from politikontroller_py.models.api import (
    APIEndpoint,
    PoliceControlResponse,
    PoliceControlsResponse,
    PoliceControlTypeEnum,
    PoliceGPSControlsResponse,
)
from politikontroller_py.utils import to_geo_json

if TYPE_CHECKING:
    from .helpers import PolitikontrollerMockServer

logger = logging.getLogger(__name__)


async def test_check(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.CHECK, "check")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.check()
        assert result == "YES"


async def test_unauthenticated_check(politikontroller_fixture: PolitikontrollerMockServer):
    politikontroller_fixture.add_politikontroller(APIEndpoint.CHECK, "check")
    async with ClientSession() as session:
        client = Client(session=session)
        with pytest.raises(AuthenticationError):
            await client.check()


async def test_authenticate(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.authenticate_user(client.user.username, client.user.password)
        assert isinstance(result, Account)


async def test_login(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    async with ClientSession() as session:
        client = politikontroller_client()
        result = await client.login(client.user.username, client.user.password, session)
        assert isinstance(result, Client)


async def test_login_error(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login_error")
    async with ClientSession() as session:
        client = politikontroller_client()
        with pytest.raises(AuthenticationError):
            await client.login(client.user.username, client.user.password, session)


async def test_login_blocked(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login_blocked")
    async with ClientSession() as session:
        client = politikontroller_client()
        with pytest.raises(AuthenticationError):
            await client.login(client.user.username, client.user.password, session)


async def test_login_not_activated(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login_not_activated")
    async with ClientSession() as session:
        client = politikontroller_client()
        with pytest.raises(AuthenticationError):
            await client.login(client.user.username, client.user.password, session)


async def test_get_controls_in_radius(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    control_ids = [59777, 59786, 59790]
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.GPS_CONTROLS, "gps_kontroller")
    for i in control_ids:
        politikontroller_fixture.add_politikontroller(
            APIEndpoint.SPEED_CONTROL,
            f"hki_{i}",
            params={"kontroll_id": i},
            repeat=2,
        )

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_controls_in_radius(lat=0, lng=0, radius=100, merge_duplicates=False)
        assert len(result) == 3
        assert all(isinstance(c, PoliceGPSControlsResponse) for c in result)
        controls = await client.get_controls_from_lists(result)
        assert len(controls) == 3


async def test_get_controls_in_radius_clustered(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    control_ids = [1000, 1001]
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(
        APIEndpoint.GPS_CONTROLS,
        "gps_kontroller_cluster",
    )
    for i in control_ids:
        politikontroller_fixture.add_politikontroller(
            APIEndpoint.SPEED_CONTROL,
            f"hki_{i}",
            params={"kontroll_id": i},
        )

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_controls_in_radius(lat=0, lng=0, radius=100)
        assert len(result) == 1
        assert all(isinstance(c, PoliceGPSControlsResponse) for c in result)
        assert result[0].duplicates[0].id == 1001


async def test_get_controls_in_radius_no_content(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.GPS_CONTROLS, "hk_empty")

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_controls_in_radius(lat=0, lng=0, radius=100)
        assert len(result) == 0


async def test_get_controls(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.SPEED_CONTROLS, "hk")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_controls(lat=0, lng=0, merge_duplicates=False)
        assert len(result) == 3
        assert all(isinstance(c, PoliceControlsResponse) for c in result)


async def test_get_controls_geo_json(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.SPEED_CONTROLS, "hk")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_controls(lat=0, lng=0)
        geo = to_geo_json(result)
        assert geo["type"] == "FeatureCollection"


async def test_get_controls_clustered(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(
        APIEndpoint.SPEED_CONTROLS,
        "hk_cluster",
    )
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_controls(lat=0, lng=0, merge_duplicates=True)
        assert len(result) == 1
        assert all(isinstance(c, PoliceControlsResponse) for c in result)


async def test_get_controls_empty(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.SPEED_CONTROLS, "hk_empty")
    politikontroller_fixture.add_politikontroller(APIEndpoint.GPS_CONTROLS, "hk_empty")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_controls(lat=0, lng=0)
        assert len(result) == 0


@pytest.mark.parametrize(
    "control_id",
    [
        59786,
    ],
)
async def test_get_control(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client, control_id
):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(
        APIEndpoint.SPEED_CONTROL, f"hki_{control_id}", params={"kontroll_id": control_id}
    )
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_control(control_id)
        assert isinstance(result, PoliceControlResponse)


async def test_get_control_types(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = client.get_control_types()
        assert isinstance(result, list)
        assert all(isinstance(c, PoliceControlTypeEnum) for c in result)


async def test_get_maps(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.GET_MY_MAPS, "hent_mine_kart")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_maps()
        assert isinstance(result, list)


async def test_get_settings(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.SETTINGS, "instillinger")
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.get_settings()
        assert isinstance(result, dict)


async def test_timeout(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: ClientResponse):
        """Response handler for this test."""
        await asyncio.sleep(2)
        return Response(body="Helluu")  # pragma: no cover

    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add(
        response=response_handler,
    )
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        client.request_timeout = 1
        with pytest.raises(PolitikontrollerTimeoutError):
            assert await client.api_request(APIEndpoint.CHECK)


async def test_http_error400(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    """Test HTTP 400 response handling."""
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add(
        response=Response(status=400),
    )

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        with pytest.raises(PolitikontrollerError):
            assert await client.check()


async def test_http_error403(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    """Test HTTP 403 response handling."""
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add(
        response=Response(status=403),
    )

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        with pytest.raises(PolitikontrollerError):
            assert await client.check()


async def test_http_error404(politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client):
    """Test HTTP 404 response handling."""
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add(
        response=Response(status=404),
    )

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        with pytest.raises(NotFoundError):
            assert await client.check()


async def test_connection_error(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    """Test unexpected error handling."""
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add(
        response=Response(text="Error", status=418),
    )

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        with pytest.raises(PolitikontrollerConnectionError):
            assert await client.check()


async def test_unexpected_error(
    politikontroller_fixture: PolitikontrollerMockServer, politikontroller_client
):
    """Test unexpected error handling."""
    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add(
        response=Response(text="Error", status=418),
    )

    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        with pytest.raises(PolitikontrollerError):
            assert await client.check()
