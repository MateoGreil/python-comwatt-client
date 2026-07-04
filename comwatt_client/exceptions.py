from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests


class ComwattError(Exception):
    """Base class for all errors raised by the Comwatt client."""

    def __init__(self, message: str | None = None, *, status_code: int | None = None, url: str | None = None, detail: str | None = None, response: requests.Response | None = None) -> None:
        self.status_code = status_code
        self.url = url
        self.detail = detail
        self.response = response
        if message is None:
            message = f"{status_code} {url}"
            if detail:
                message = f"{message}: {detail}"
        super().__init__(message)


class ComwattAuthError(ComwattError):
    """The session is invalid or login failed (HTTP 401, or a failed authenticate()).
    Callers should re-authenticate."""


class ComwattAPIError(ComwattError):
    """Any other unexpected HTTP status from the Comwatt API."""
