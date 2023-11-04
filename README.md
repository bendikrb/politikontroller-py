# politikontroller-py

## Install

```bash
pip3 install politikontroller-py
```

## Usage

```python
from politikontroller_py import Client
from politikontroller_py.models import Account

# A valid registered user @ politikontroller.no
user = Account(
    username="4790112233",  # Include 2 digit prefix - or else DEFAULT_COUNTRY is assumed
    password="super-secret",
)

client = Client(user)

police_controls = client.get_controls(63, 11)

```


## CLI tool

```bash
$ politikontroller --help
Usage: politikontroller [OPTIONS] COMMAND [ARGS]...

  Username and password can be defined using env vars:

  POLITIKONTROLLER_USERNAME
  POLITIKONTROLLER_PASSWORD

Options:
  -u, --username TEXT  Username (i.e. phone number)  [required]
  -p, --password TEXT  Password  [required]
  --debug              Set logging level to DEBUG
  --help               Show this message and exit.

Commands:
  exchange-points      exchange points (?)
  get-control          get details on a control.
  get-controls         get a list of all active controls.
  get-controls-radius  get all active controls inside a radius.
  get-maps             get own maps.
```
