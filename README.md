# politikontroller-py

[![GitHub Release][releases-shield]][releases]
[![Python Versions][py-versions-shield]][py-versions]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE)
![Made with Love in Norway][madewithlove-shield]

[![Build Status][build-shield]][build]
[![Code coverage][codecov-shield]][codecov]


## Install

```bash
pip install politikontroller-py
```

## Usage

### Basic usage
```python
from politikontroller_py import Client

client = Client.initialize("4790112233", "super-secret")

async def main():
    police_controls = await client.get_controls(63, 11)
    print(police_controls)
```


### With account
```python
from politikontroller_py import Client
from politikontroller_py.models import Account

# A valid registered user @ politikontroller.no
user = Account(
    username="4790112233",  # Include 2 digit prefix - or else DEFAULT_COUNTRY is assumed
    password="super-secret",
)

client = Client(user)

async def main():
    police_controls = await client.get_controls(63, 11)
    print(police_controls)
```


### With session
```python
from aiohttp import ClientSession
from politikontroller_py import Client

async def main():
    async with ClientSession() as session:
        client = Client.initialize("4790112233", "super-secret", session=session)
        police_controls = await client.get_controls(63, 11)
        print(police_controls)
```


## CLI tool

```bash
$ politikontroller --help
Usage: politikontroller [OPTIONS] COMMAND [ARGS]...

  Connect to politikontroller.no and fetch data in a simple way.

  Username and password can be defined using env vars.

  POLITIKONTROLLER_USERNAME POLITIKONTROLLER_PASSWORD

Options:
  -u, --username TEXT  Username (i.e. phone number)  [required]
  -p, --password TEXT  Password  [required]
  --debug              Set logging level to DEBUG
  --help               Show this message and exit.

Commands:
  account-auth         activate account
  account-auth-sms     activate account by sms
  account-register     register new account
  account-send-sms     send activation sms
  check                server health check.
  exchange-points      exchange points (?)
  get-control          get details on a control.
  get-control-types    get a list of control types.
  get-controls         get a list of all active controls.
  get-controls-radius  get all active controls inside a radius.
  get-maps             get own maps.
  get-settings         get own settings.

```


[license-shield]: https://img.shields.io/github/license/bendikrb/politikontroller-py.svg
[license]: https://github.com/bendikrb/politikontroller-py/blob/main/LICENSE
[releases-shield]: https://img.shields.io/pypi/v/politikontroller-py
[releases]: https://github.com/bendikrb/politikontroller-py/releases
[build-shield]: https://github.com/bendikrb/politikontroller-py/actions/workflows/test.yaml/badge.svg
[build]: https://github.com/bendikrb/politikontroller-py/actions/workflows/test.yaml
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[py-versions-shield]: https://img.shields.io/pypi/pyversions/politikontroller-py
[py-versions]: https://pypi.org/project/politikontroller-py/
[codecov-shield]: https://codecov.io/gh/bendikrb/politikontroller-py/graph/badge.svg?token=IXLJ3WR4ES
[codecov]: https://codecov.io/gh/bendikrb/politikontroller-py
[madewithlove-shield]: https://madewithlove.now.sh/no?heart=true&colorB=%233584e4
