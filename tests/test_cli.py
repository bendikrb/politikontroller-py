import contextlib
import subprocess
import sys

import pytest

import politikontroller_py.cli
from politikontroller_py.models.api import APIEndpoint

from .helpers import PolitikontrollerMockServer

ARGS_USER_PW = ["-u", "4747474747", "-p", "securepassword123"]
FIXTURE_CLI_HELP = "Connect to politikontroller.no"


def test_run_entrypoint():
    """Test if the entrypoint is installed correctly."""
    result = subprocess.run(["politikontroller", "--help"], capture_output=True, text=True)

    assert FIXTURE_CLI_HELP in result.stdout
    assert result.returncode == 0


def test_run_module():
    """Test if the module can be run as a python module."""
    result = subprocess.run(
        ["python", "-m", "politikontroller_py.cli", "--help"], capture_output=True, text=True
    )

    assert FIXTURE_CLI_HELP in result.stdout
    assert result.returncode == 0


async def test_check(capsys: pytest.CaptureFixture, politikontroller_fixture: PolitikontrollerMockServer):
    """Test the status command text output filtered by VIN."""

    politikontroller_fixture.add_politikontroller(APIEndpoint.LOGIN, "login")
    politikontroller_fixture.add_politikontroller(APIEndpoint.CHECK, "check")

    sys.argv = ["politikontroller", *ARGS_USER_PW, "check"]
    with contextlib.suppress(SystemExit):
        await politikontroller_py.cli.amain()
    result = capsys.readouterr()

    assert "YES" in result.out
