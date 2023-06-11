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
    phone_number=90112233,
    phone_prefix=47,
    password="super-secret",
)
# Alternative;
user = Account(username="4790112233", password="super-secret")

client = Client(user)

police_controls = client.get_controls(63, 11)

```


## CLI tool

```bash
$ politikontroller 
Usage: politikontroller [OPTIONS] COMMAND [ARGS]...

  Username and password can be defined using env vars:

  POLITIKONTROLLER_USERNAME POLITIKONTROLLER_PASSWORD

Options:
  -u, --username INTEGER  Username (i.e. phone number)  [required]
  --password TEXT         Password  [required]
  --help                  Show this message and exit.

Commands:
  get-control          get details on a control.
  get-controls         get a list of all active controls.
  get-controls-radius  get all active controls inside a radius.
```
