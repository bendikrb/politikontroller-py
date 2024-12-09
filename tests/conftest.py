from __future__ import annotations

import asyncio
import logging
from typing import Callable, Generator

import aresponses
import pytest

from politikontroller_py import Account, Client

from .helpers import PolitikontrollerMockServer

_LOGGER = logging.getLogger(__name__)


@pytest.fixture
async def politikontroller_client(default_login_details) -> Callable[..., Client]:
    """Return Politikontroller Client."""

    def _politikontroller_client(
        credentials: Account | None = None,
        load_default_login_details: bool = True,
    ) -> Client:
        login_details = default_login_details if load_default_login_details is True else credentials
        return Client.initialize(login_details.username, login_details.password)

    return _politikontroller_client


@pytest.fixture
def default_login_details():
    return Account(username="4747474747", password="securepassword123")


@pytest.fixture
async def politikontroller_fixture(
    request: pytest.FixtureRequest,
) -> Generator[aresponses.ResponsesMockServer, None, None]:
    """Patch Politikontroller API calls."""
    loop = asyncio.get_running_loop()
    async with PolitikontrollerMockServer(loop=loop) as server:
        yield server
