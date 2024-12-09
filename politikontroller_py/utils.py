from __future__ import annotations

import base64
from datetime import datetime, time as dt_time
from logging import getLogger
from math import atan2, cos, sin, sqrt
import random
import re
import string
import time
from typing import TYPE_CHECKING, TypeVar

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from geojson.mapping import to_mapping

from .constants import (
    CRYPTO_K1,
    CRYPTO_K2,
    DEFAULT_MAX_DISTANCE,
)

if TYPE_CHECKING:
    from .models.api import PoliceControl, PoliceControlPoint

    PC = TypeVar("PC", bound=PoliceControl)

_LOGGER = getLogger(__name__)
JUNK_CHARS = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x10\x0f"


def get_random_string(length: int, letters: str | None = None) -> str:
    """Generate a random string of given length using given letters."""
    if letters is None:
        letters = string.ascii_uppercase + string.digits
    return "".join(random.choice(letters) for _ in range(length))


def get_unix_timestamp():
    """Get current unix timestamp with 10 seconds added."""
    return int(time.time()) + 10


def aes_encrypt(input_str: str):
    """Encrypts a string using AES encryption with given key and initialization vector.
    Returns base64-encoded result.
    """
    key = base64.b64decode(CRYPTO_K2)
    iv = base64.b64decode(CRYPTO_K1)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    length = 16 - (len(input_str) % 16)
    input_b = bytes(input_str, "utf-8") + bytes([length]) * length
    input_padded = pad(input_b, AES.block_size)
    return base64.b64encode(cipher.encrypt(input_padded)).decode()


def aes_decrypt(enc_base64: str):
    """Decrypts AES encrypted data using a given key and initialization vector."""
    enc_data = base64.b64decode(enc_base64)
    key = base64.b64decode(CRYPTO_K2)
    iv = base64.b64decode(CRYPTO_K1)
    decipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext_padded = decipher.decrypt(enc_data)
    return unpad(ciphertext_padded, AES.block_size).decode().strip(JUNK_CHARS)


def map_response_data(
    data: str, map_keys: list[str | None], multiple=False
) -> list[dict[str, str]] | dict[str, str]:
    """Convert a cvs-like string into dictionaries."""

    def row_to_dict(row) -> dict[str, str]:
        r = dict(zip(map_keys, row.split("|")))
        return {k: r[k] for k in r if isinstance(k, str)}

    if multiple:
        return list(map(row_to_dict, list(data.split("#"))))

    return row_to_dict(data)


def unmap_response_data(
    data: list[dict[str, any]] | dict[str, any], map_keys: list[str | None]
) -> str:  # pragma: no cover
    """Convert dictionaries into a cvs-like string."""

    def dict_to_row(d: dict[str, any]) -> str:
        row = [str(d.get(k, "")) if k is not None else "" for k in map_keys]
        return "|".join(row)

    if isinstance(data, list):
        return "#".join(map(dict_to_row, data))

    return dict_to_row(data)


def parse_datetime_like(v: str) -> int | None:
    """Parse datetime like string to unix timestamp."""
    if isinstance(v, int) and v != 0:
        return v
    if len(v) == 0 or (v.isnumeric() and int(v) == 0):
        return None
    return int(parse_time_format(v))


def parse_time_format(text: str) -> int | str:
    """Parse time format to unix timestamp."""
    today = datetime.now().astimezone()
    try:
        # Match "%d.%m - %H:%M" this way due to failure on leap days using strptime.
        if m := re.match(r"(\d{2})\.(\d{2}) - (\d{2}):(\d{2})", text):
            return int(
                datetime.fromisoformat(f"{today.year}-{m[2]}-{m[1]}T{m[3]}:{m[4]}:00")
                .astimezone()
                .timestamp()
            )
    except ValueError:  # pragma: no cover
        pass

    try:
        return int(
            datetime.combine(
                today,
                dt_time.fromisoformat(text),
            )
            .astimezone()
            .timestamp()
        )
    except ValueError:  # pragma: no cover
        pass

    try:  # pragma: no cover
        text = re.sub(r"(\d{2}:\d{2})(?: \(\d+ ganger\))?", "\\1", text)
        return int(
            datetime.strptime(text, "%H:%M")
            .astimezone()
            .replace(
                year=today.year,
                month=today.month,
                day=today.day,
            )
            .timestamp()
        )
    except ValueError:  # pragma: no cover
        pass
    return text  # pragma: no cover


def calculate_distance(point1: PoliceControlPoint, point2: PoliceControlPoint) -> float:
    """Calculate distance between two points."""
    earth_radius = 6373.0  # Approximate radius of earth in km
    lat1, lon1 = point1.coordinates(as_radian=True)
    lat2, lon2 = point2.coordinates(as_radian=True)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def average_points(p1: PoliceControlPoint, p2: PoliceControlPoint) -> tuple[float, float]:
    """Average two points."""
    return (p1.lat + p2.lat) / 2, (p1.lng + p2.lng) / 2


def merge_duplicate_controls(controls: list[PC], max_distance: float | None = None) -> list[PC]:
    """Merge duplicate controls."""
    if max_distance is None:
        max_distance = DEFAULT_MAX_DISTANCE
    merged_controls = []
    skip_indices = set()

    for i, control1 in enumerate(controls):
        if i in skip_indices:
            continue

        for j, control2 in enumerate(controls):
            if i == j or j in skip_indices:
                continue

            distance = calculate_distance(control1.point, control2.point)
            if distance <= max_distance and control1.type == control2.type:
                control1 = control1.merge_with(control2)  # noqa: PLW2901

                skip_indices.add(j)

        merged_controls.append(control1)

    return merged_controls


def to_geo_json(controls: list[PC]):
    return {
        "type": "FeatureCollection",
        "features": [to_mapping(c) for c in controls],
    }
