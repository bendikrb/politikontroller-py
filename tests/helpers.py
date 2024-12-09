from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from aresponses import Response, ResponsesMockServer
from aresponses.main import Route

# noinspection PyProtectedMember
from aresponses.utils import ANY, _text_matches_pattern

from politikontroller_py.models.api import APIEndpoint
from politikontroller_py.utils import aes_decrypt

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load a fixture."""
    path = FIXTURE_DIR / f"{name}.txt"
    if not path.exists():  # pragma: no cover
        raise FileNotFoundError(f"Fixture {name} not found")
    return path.read_text(encoding="utf-8")


class CustomRoute(Route):
    """Custom route for aresponses."""

    def __init__(
        self,
        method_pattern=ANY,
        host_pattern=ANY,
        path_pattern=ANY,
        path_qs=None,
        body_pattern=ANY,
        match_querystring=False,
        match_partial_query=True,
        repeat=1,
    ):
        super().__init__(method_pattern, host_pattern, path_pattern, body_pattern, match_querystring, repeat)
        if path_qs is not None:
            self.path_qs = urlencode({k: v for k, v in path_qs.items() if v is not None})
            self.match_querystring = True
            self.match_partial_query = match_partial_query

    async def matches(self, request):
        """Check if the request matches this route."""
        path_to_match = urlparse(request.path_qs)
        query_to_match = parse_qs(aes_decrypt(path_to_match.query))
        parsed_query = parse_qs(self.path_qs) if self.path_qs else {}

        if not _text_matches_pattern(self.host_pattern, request.host):
            return False

        if self.match_querystring:
            if not self.match_partial_query and query_to_match != parsed_query:
                return False
            for key, value in parsed_query.items():
                if key not in query_to_match or query_to_match[key] != value:
                    return False

        if not _text_matches_pattern(self.method_pattern, request.method):  # noqa: SIM103
            return False

        return True


class PolitikontrollerMockServer(ResponsesMockServer):
    def add_politikontroller(
        self,
        endpoint: APIEndpoint,
        fixture: str,
        params: dict | None = None,
        **kwargs,
    ):
        if params is None:
            params = {}
        self.add(
            response=Response(text=load_fixture(fixture)),
            route=CustomRoute(
                path_qs={"p": endpoint, **params},
            ),
            **kwargs,
        )


def setup_auth_mocks(aresponses: ResponsesMockServer):
    aresponses.add(
        response=Response(text=load_fixture("login")),
        route=CustomRoute(
            path_qs={"p": APIEndpoint.LOGIN},
        ),
    )
