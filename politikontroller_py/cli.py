""" CLI tool """

from tabulate import tabulate
from rich import print as rprint
import click

from politikontroller_py import Client
from politikontroller_py.models import (
    PoliceControl,
)
from politikontroller_py.exceptions import AuthenticationError

TABULATE_DEFAULTS = {
    'tablefmt': 'rounded_grid',
}

client = Client()


@click.group()
@click.option('--username', '-u', envvar='POLITIKONTROLLER_USERNAME', type=int,
              required=True, help="Username (i.e. phone number)")
@click.password_option(envvar='POLITIKONTROLLER_PASSWORD', type=str, required=True,
                       confirmation_prompt=False, help='Password')
def cli(username: int, password: str):
    """
    Username and password can be defined using env vars:

    POLITIKONTROLLER_USERNAME
    POLITIKONTROLLER_PASSWORD
    """
    try:
        client.authenticate_user(47, username, password)
    except AuthenticationError as err:
        raise click.BadParameter("Authentication error",
                                 param_hint=["--username", "--password"]) from err


@cli.command('get-controls', short_help='get a list of all active controls.')
@click.option('--lat', required=True, help='Your position (latitude)')
@click.option('--lng', required=True, help='Your position (longitude)')
def get_controls(lat: float, lng: float):
    controls = client.get_controls(lat, lng)
    click.echo(tabulate(controls, **TABULATE_DEFAULTS))


@cli.command('get-controls-radius',
             short_help='get all active controls inside a radius.')
@click.option('--lat', type=float, required=True, help='Radius center (latitude)')
@click.option('--lng', type=float, required=True, help='Radius center (longitude)')
@click.option('--radius', type=int, required=True, metavar='km',
              help='Radius size in kilometers')
@click.option('--speed', type=int, required=False, metavar='km/h',
              help='Speed, unknown what this does')
def get_controls_in_radius(lat: float, lng: float, radius: int, speed: int):
    controls = client.get_controls_in_radius(lat, lng, radius, speed)
    click.echo(tabulate(controls, **TABULATE_DEFAULTS))


@cli.command('get-control', short_help='get details on a control.')
@click.argument('control_id', type=int, required=True)
def get_control(control_id: int):
    control = PoliceControl(**client.get_control(control_id))
    rprint(control)
