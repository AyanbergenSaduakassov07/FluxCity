"""Canonical JSON hashing: equal content gives an equal hash regardless of field order."""

import hashlib
import json
import re
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(model: BaseModel, exclude: Iterable[str] = ()) -> str:
    return sha256_bytes(canonical_json(model.model_dump(mode="json", exclude=set(exclude))))
