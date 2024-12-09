"""CLI tool."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import anyio
import asyncclick as click
from tabulate import tabulate

from politikontroller_py import Client
from politikontroller_py.exceptions import AuthenticationError

if TYPE_CHECKING:
    from asyncclick.core import Context

TABULATE_DEFAULTS = {
    "tablefmt": "rounded_grid",
}


def tabulate_model(data: list[dict], keys: list[str]) -> list[list[str]]:
    result = [keys]
    for item in data:
        row = [item.get(key) for key in keys]
        result.append(row)
    return result


@click.group()
@click.option(
    "--username",
    "-u",
    envvar="POLITIKONTROLLER_USERNAME",
    type=str,
    required=True,
    help="Username (i.e. phone number)",
)
@click.password_option(
    "--password",
    "-p",
    envvar="POLITIKONTROLLER_PASSWORD",
    type=str,
    required=True,
    confirmation_prompt=False,
    help="Password",
)
@click.option("--debug", is_flag=True, help="Set logging level to DEBUG")
@click.pass_context
async def cli(ctx: Context, username: str, password: str, debug: bool):
    """Connect to politikontroller.no and fetch data in a simple way.

    Username and password can be defined using env vars.

    POLITIKONTROLLER_USERNAME
    POLITIKONTROLLER_PASSWORD
    """
    configure_logging(debug)

    ctx.obj = client = Client()

    try:
        user = await client.authenticate_user(username, password)
    except AuthenticationError as err:
        raise click.BadParameter(str(err), param_hint="--username, --password") from err
    click.echo(user)


@cli.command("check", short_help="server health check.")
@click.pass_obj
async def check(obj: Client):
    res = await obj.check()
    click.echo(res)


@cli.command("get-control-types", short_help="get a list of control types.")
@click.pass_obj
async def get_control_types(obj):
    types = await obj.get_control_types()
    click.echo(tabulate([t.to_dict() for t in types], **TABULATE_DEFAULTS))


@cli.command("get-controls", short_help="get a list of all active controls.")
@click.option("--lat", required=True, help="Your position (latitude)")
@click.option("--lng", required=True, help="Your position (longitude)")
@click.pass_obj
async def get_controls(obj, lat: float, lng: float):
    controls = await obj.get_controls(lat, lng)
    click.echo(tabulate([d.to_dict() for d in controls], **TABULATE_DEFAULTS))


@cli.command("get-controls-radius", short_help="get all active controls inside a radius.")
@click.option("--lat", type=float, required=True, help="Radius center (latitude)")
@click.option("--lng", type=float, required=True, help="Radius center (longitude)")
@click.option("--radius", type=int, required=True, metavar="km", help="Radius size in kilometers")
@click.option("--speed", type=int, required=False, metavar="km/h", help="Speed, unknown what this does")
@click.pass_obj
async def get_controls_in_radius(obj: Client, lat: float, lng: float, radius: int, speed: int):
    _controls = await obj.get_controls_in_radius(lat, lng, radius, speed)
    controls = await obj.get_controls_from_lists(_controls)

    lists = tabulate_model(
        [c.to_dict() for c in controls],
        [
            "id",
            "timestamp",
            "type",
            "municipality",
            "description",
            "point",
        ],
    )
    click.echo(tabulate(lists, headers="firstrow", **TABULATE_DEFAULTS))


@cli.command("get-control", short_help="get details on a control.")
@click.argument("control_id", type=int, required=True)
@click.pass_obj
async def get_control(obj: Client, control_id: int):
    control = await obj.get_control(control_id)
    click.echo(
        tabulate(
            tabulate_model(
                [control.to_dict()],
                [
                    "id",
                    "county",
                    "municipality",
                    "description",
                    "type",
                    "lat",
                    "lng",
                    "timestamp",
                ],
            ),
            headers="firstrow",
            **TABULATE_DEFAULTS,
        )
    )


@cli.command("get-maps", short_help="get own maps.")
@click.pass_obj
async def get_maps(obj: Client):
    maps = await obj.get_maps()
    click.echo(tabulate([m.to_dict() for m in maps], **TABULATE_DEFAULTS))


@cli.command("get-settings", short_help="get own settings.")
@click.pass_obj
async def get_settings(obj: Client):
    settings = await obj.get_settings()
    click.echo(tabulate(settings, **TABULATE_DEFAULTS))


@cli.command("exchange-points", short_help="exchange points (?)")
@click.pass_obj
async def exchange_points(obj: Client):
    res = await obj.exchange_points()
    click.echo(tabulate(res, **TABULATE_DEFAULTS))


@cli.command("account-send-sms", short_help="send activation sms")
@click.pass_obj
async def account_send_sms(obj: Client):
    res = await obj.account_send_sms()
    click.echo(res)


@cli.command("account-auth-sms", short_help="activate account by sms")
@click.pass_obj
async def account_auth_sms(obj: Client):
    res = await obj.account_auth_sms()
    click.echo(res)


@cli.command("account-auth", short_help="activate account")
@click.argument("code", type=str, required=True)
@click.argument("uid", type=int, required=True)
@click.pass_obj
async def account_auth(obj: Client, code: str, uid: int):
    res = await obj.account_auth(auth_code=code, uid=uid)
    click.echo(res)


@cli.command("account-register", short_help="register new account")
@click.argument("phone", type=int, required=True)
@click.argument("password", type=str, required=True)
@click.argument("name", type=str, required=True)
@click.argument("country", type=str, required=True)
@click.pass_obj
async def account_register(
    obj: Client,
    phone: int,
    password: str,
    name: str,
    country: str,
):
    res = await obj.account_register(
        phone_number=phone,
        password=password,
        name=name,
        country=country,
    )
    click.echo(res)


def configure_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level)


async def amain(args: list[str] | None = None):
    await cli.main(args)


def main():
    # noinspection PyTypeChecker
    anyio.run(amain)


if __name__ == "__main__":
    main()
