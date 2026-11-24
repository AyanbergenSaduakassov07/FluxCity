"""ULID generation (sortable by creation time) and validation, stdlib only."""

import re
import secrets
import time

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32
ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def new_id() -> str:
    value = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    return "".join(_ALPHABET[(value >> shift) & 31] for shift in range(125, -1, -5))


def is_id(value: str) -> bool:
    return bool(ULID_RE.match(value))
