"""Tests for NrkPodcastAPI."""

from __future__ import annotations

import logging

from aiohttp import ClientSession
from aresponses import Response, ResponsesMockServer

from politikontroller_py.models.api import APIEndpoint

from .helpers import CustomRoute, load_fixture

logger = logging.getLogger(__name__)


async def test_check(aresponses: ResponsesMockServer, politikontroller_client):
    aresponses.add(
        response=Response(text=load_fixture("check")),
        route=CustomRoute(
            path_qs={"p": APIEndpoint.CHECK},
        ),
    )
    async with ClientSession() as session:
        client = politikontroller_client()
        client.session = session
        result = await client.check()
        assert result == "YES"
