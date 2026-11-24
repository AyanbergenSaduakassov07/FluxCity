"""Typed errors mapped to problem+json by the API layer."""

from typing import Any


class FluxError(Exception):
    status = 500

    def __init__(self, code: str, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail or {}


class NotFound(FluxError):
    status = 404


class Conflict(FluxError):
    status = 409


class InvalidInput(FluxError):
    status = 422
