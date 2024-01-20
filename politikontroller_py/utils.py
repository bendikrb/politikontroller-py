from __future__ import annotations

import base64
from datetime import datetime, time as dt_time
from json import JSONDecoder, JSONEncoder
from logging import getLogger
import random
import re
import string
import time

from Crypto.Cipher import AES

from .constants import (
    CLIENT_OS,
    CLIENT_VERSION_NUMBER,
    CRYPTO_K1,
    CRYPTO_K2,
)

_LOGGER = getLogger(__name__)


def get_random_string(length: int, letters: str | None = None) -> str:
    if letters is None:
        letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))  # noqa: S311


def generate_device_id():
    return get_random_string(16, letters=string.digits + 'abcdef')


def get_unix_timestamp():
    return int(time.time()) + 10


def hash_credentials(credentials: dict):
    creds = bytes(JSONEncoder().encode(credentials), 'utf-8')
    return base64.b64encode(creds).decode()


def unhash_credentials(credentials: str):
    creds = base64.b64decode(credentials).decode()
    return JSONDecoder().decode(creds)


def aes_encrypt(input_str: str):
    """Encrypts a string using AES encryption with given key and initialization vector.
    Returns base64-encoded result.
    """
    key = base64.b64decode(CRYPTO_K2)
    iv = base64.b64decode(CRYPTO_K1)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    length = 16 - (len(input_str) % 16)
    input_b = bytes(input_str, 'utf-8') + bytes([length]) * length
    return base64.b64encode(cipher.encrypt(input_b)).decode()


def aes_decrypt(enc_base64: str):
    """Decrypts AES encrypted data using a given key and initialization vector."""
    enc_data = base64.b64decode(enc_base64)
    key = base64.b64decode(CRYPTO_K2)
    iv = base64.b64decode(CRYPTO_K1)
    decipher = AES.new(key, AES.MODE_CBC, iv)
    return decipher.decrypt(enc_data).decode()


def get_query_params(params: dict):
    """Generate a query dictionary with random and predefined values.
    Replaces special characters in the values with hyphens.
    """
    query = {
        'bac': get_random_string(10),
        'z': int(time.time()) + 10,
        'version': CLIENT_VERSION_NUMBER,
        'os': CLIENT_OS,
        **params,
        'tt': get_random_string(5),
    }
    for k, v in query.items():
        if k in ['bac', 'z', 'version', 'os', 'tt']:
            query[k] = re.sub(r"[|#\\\"]", "-", str(v))
    return query


def map_response_data(
    data: str,
    map_keys: list[str | None],
    multiple=False
) -> list[dict[str, str]] | dict[str, str]:
    """Convert a cvs-like string into dictionaries."""

    def row_to_dict(row) -> dict[str, str]:
        r = dict(zip(map_keys,
                     row.split('|')))  # pylint: disable=modified-iterating-list
        return {k: r[k] for k in r if isinstance(k, str)}

    if multiple:
        return list(map(row_to_dict, list(data.split('#'))))

    return row_to_dict(data)


def parse_time_format(text: str):
    today = datetime.now().astimezone()
    try:
        return int(
            datetime.strptime(text, "%d.%m - %H:%M").astimezone().replace(
                year=today.year,
            ).timestamp()
        )
    except ValueError:
        pass

    try:
        return int(
            datetime.combine(
                today,
                dt_time.fromisoformat(text),
            ).astimezone().timestamp()
        )
    except ValueError:
        pass

    try:
        text = re.sub(r"(\d{2}:\d{2})(?: \(\d+ ganger\))?", "\\1", text)
        return int(
            datetime.strptime(text, "%H:%M").astimezone().replace(
                year=today.year,
                month=today.month,
                day=today.day,
            ).timestamp()
        )
    except ValueError:
        pass
    return text
