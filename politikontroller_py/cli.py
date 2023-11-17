"""CLI tool."""

import logging

import anyio
import asyncclick as click
from asyncclick.core import Context
from tabulate import tabulate

from politikontroller_py import Client
from politikontroller_py.exceptions import AuthenticationError
from politikontroller_py.models import (
    PoliceControl,
)

TABULATE_DEFAULTS = {
    'tablefmt': 'rounded_grid',
}


@click.group()
@click.option('--username', '-u', envvar='POLITIKONTROLLER_USERNAME', type=str,
              required=True, help='Username (i.e. phone number)')
@click.password_option('--password',
                       '-p',
                       envvar='POLITIKONTROLLER_PASSWORD',
                       type=str,
                       required=True,
                       confirmation_prompt=False,
                       help='Password')
@click.option('--debug', is_flag=True, help='Set logging level to DEBUG')
@click.pass_context
async def cli(ctx: Context, username: str, password: str, debug: bool):
    """Username and password can be defined using env vars:

    POLITIKONTROLLER_USERNAME
    POLITIKONTROLLER_PASSWORD
    """
    configure_logging(debug)

    ctx.obj = client = Client()

    try:
        await client.authenticate_user(username, password)
    except AuthenticationError as err:
        raise click.BadParameter(str(err), param_hint="--username, --password") from err


@cli.command('get-controls', short_help='get a list of all active controls.')
@click.option('--lat', required=True, help='Your position (latitude)')
@click.option('--lng', required=True, help='Your position (longitude)')
@click.pass_obj
async def get_controls(obj, lat: float, lng: float):
    controls = await obj.get_controls(lat, lng)
    click.echo(tabulate(controls, **TABULATE_DEFAULTS))


@cli.command('get-controls-radius',
             short_help='get all active controls inside a radius.')
@click.option('--lat', type=float, required=True, help='Radius center (latitude)')
@click.option('--lng', type=float, required=True, help='Radius center (longitude)')
@click.option('--radius', type=int, required=True, metavar='km',
              help='Radius size in kilometers')
@click.option('--speed', type=int, required=False, metavar='km/h',
              help='Speed, unknown what this does')
@click.pass_obj
async def get_controls_in_radius(obj, lat: float, lng: float, radius: int, speed: int):
    controls = await obj.get_controls_in_radius(lat, lng, radius, speed)
    click.echo(tabulate(controls, **TABULATE_DEFAULTS))


@cli.command('get-control', short_help='get details on a control.')
@click.argument('control_id', type=int, required=True)
@click.pass_obj
async def get_control(obj, control_id: int):
    control = PoliceControl.parse_obj(await obj.get_control(control_id))
    click.echo(tabulate(control, **TABULATE_DEFAULTS))


@cli.command('get-maps', short_help='get own maps.')
@click.pass_obj
async def get_maps(obj):
    maps = await obj.get_maps()
    print(maps)


@cli.command('exchange-points', short_help='exchange points (?)')
@click.pass_obj
async def exchange_points(obj):
    res = await obj.exchange_points()
    print(res)


def configure_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level)


async def main():
    await cli.main()

if __name__ == '__main__':
    anyio.run(main)
