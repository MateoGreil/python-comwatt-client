from __future__ import annotations

import requests

from types import TracebackType
from typing import Any, TypeVar

from .exceptions import ComwattAPIError, ComwattAuthError, ComwattError


def _response_detail(response: requests.Response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        return body.get("detail")
    return None


def _api_error(response: requests.Response) -> ComwattError:
    detail = _response_detail(response)
    exc_cls = ComwattAuthError if response.status_code == 401 else ComwattAPIError
    return exc_cls(status_code=response.status_code, url=response.url, detail=detail, response=response)


_C = TypeVar("_C", bound="_BaseClient")


class _BaseClient:
    def __init__(self, timeout: float = 30, auto_reauth: bool = True) -> None:
        self.base_url = 'https://energy.comwatt.com/api'
        self.session = requests.Session()
        self.timeout = timeout
        self.auto_reauth = auto_reauth
        self._username: str | None = None
        self._auth_hash: str | None = None

    def _post_authent(self, username: str, password_hash: str) -> None:
        url = f'{self.base_url}/v1/authent'
        data = {'username': username, 'password': password_hash}

        response = self.session.post(url, json=data, timeout=self.timeout)

        if response.status_code != 200:
            detail = _response_detail(response)
            raise ComwattAuthError(status_code=response.status_code, url=response.url, detail=detail, response=response)

        if not self.session.cookies.get("cwt_session"):
            raise ComwattAuthError("Authentication succeeded (HTTP 200) but no cwt_session cookie was set")

    def _reauthenticate(self) -> None:
        if self._username and self._auth_hash:
            self._post_authent(self._username, self._auth_hash)
        else:
            raise ComwattAuthError("Session expired and no stored credentials to re-authenticate")

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f'{self.base_url}{path}'
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if response.status_code == 200:
            return response

        if response.status_code == 401 and self.auto_reauth and self._username and self._auth_hash:
            self._reauthenticate()
            retry_response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            if retry_response.status_code == 200:
                return retry_response
            raise _api_error(retry_response)

        raise _api_error(response)

    def close(self) -> None:
        """
        Releases the local HTTP resources held by the client.

        This only closes the local `requests.Session` (its connection pool
        and sockets). It does not perform any network call, so it does not
        log out server-side (no `POST /v1/logout` is issued) and does not
        invalidate the Comwatt server session.

        Safe to call multiple times.

        Args:
            None

        Returns:
            None

        """

        self.session.close()

    def __enter__(self: _C) -> _C:
        """
        Enters the runtime context for this client.

        Args:
            None

        Returns:
            This client instance.

        """

        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """
        Exits the runtime context, closing the client's local resources.

        Args:
            exc_type (type): The exception type, if any.
            exc_val (Exception): The exception instance, if any.
            exc_tb (traceback): The exception traceback, if any.

        Returns:
            None

        """

        self.close()
