from __future__ import annotations

import requests
import threading

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit
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
    if isinstance(body, list):
        codes = []
        for entry in body:
            if not isinstance(entry, dict):
                continue
            code = entry.get("code") or (entry.get("codes") or [None])[0] or entry.get("defaultMessage")
            if code:
                codes.append(str(code))
        return ", ".join(codes) if codes else None
    return None


def _parse_session_expiry(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _error_class(status_code: int, *, auth_context: bool = False) -> type[ComwattError]:
    """
    Maps an HTTP status to the exception class to raise.

    401 is always an authentication failure. 403 means "bad credentials"
    only on the login endpoint itself (`auth_context=True`); anywhere else
    it is an authorization failure and stays a `ComwattAPIError`.

    Args:
        status_code (int): The HTTP status of the response.
        auth_context (bool): Whether the failing request is the login
            call itself (default: False).

    Returns:
        type: `ComwattAuthError` or `ComwattAPIError`.

    """
    if status_code == 401:
        return ComwattAuthError
    if auth_context and status_code == 403:
        return ComwattAuthError
    return ComwattAPIError


def _api_error(response: requests.Response, *, auth_context: bool = False) -> ComwattError:
    detail = _response_detail(response)
    exc_cls = _error_class(response.status_code, auth_context=auth_context)
    return exc_cls(status_code=response.status_code, url=response.url, detail=detail, response=response)


_C = TypeVar("_C", bound="_BaseClient")

_REAUTH_MARGIN = timedelta(seconds=30)

_MAX_PAGINATION_PAGES = 1000


class _BaseClient:
    def __init__(self, timeout: float = 30, auto_reauth: bool = True) -> None:
        self.base_url = 'https://energy.comwatt.com/api'
        self.session = requests.Session()
        self.timeout = timeout
        self.auto_reauth = auto_reauth
        self._username: str | None = None
        self._auth_hash: str | None = None
        self._session_expires_at: datetime | None = None
        self._reauth_lock = threading.Lock()

    def _post_authent(self, username: str, password_hash: str) -> None:
        url = f'{self.base_url}/v1/authent'
        data = {'username': username, 'password': password_hash}

        response = self.session.post(url, json=data, timeout=self.timeout)

        if response.status_code != 200:
            raise _api_error(response, auth_context=True)

        if not self.session.cookies.get("cwt_session"):
            raise ComwattAPIError("Authentication succeeded (HTTP 200) but no cwt_session cookie was set")

        self._session_expires_at = _parse_session_expiry(response.headers.get("x-cwt-token"))

    def _reauthenticate(self) -> None:
        """
        Re-authenticates with the stored credentials.

        Concurrent calls are serialized: at most one login runs at a
        time, and a caller that acquires the lock while the session is
        already fresh (another thread just re-authenticated) skips its
        own login. Freshness is judged from `session_expires_at`; when
        the server omits the `x-cwt-token` header, waiters cannot
        detect the refresh and each performs a serialized login.

        Args:
            None

        Returns:
            None

        Raises:
            ComwattAuthError: If no credentials are stored.

        """
        if not (self._username and self._auth_hash):
            raise ComwattAuthError("Session expired and no stored credentials to re-authenticate")
        with self._reauth_lock:
            expires_at = self._session_expires_at
            if expires_at is not None and datetime.now(timezone.utc) < expires_at - _REAUTH_MARGIN:
                return
            self._post_authent(self._username, self._auth_hash)

    def _reauthenticate_if_expired(self) -> None:
        if not (self.auto_reauth and self._username and self._auth_hash):
            return
        expires_at = self._session_expires_at
        if expires_at is not None and datetime.now(timezone.utc) >= expires_at - _REAUTH_MARGIN:
            self._reauthenticate()

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        self._reauthenticate_if_expired()
        url = path if path.startswith(("http://", "https://")) else f'{self.base_url}{path}'
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

    def _paginate(self, path: str) -> list[dict[str, Any]]:
        """
        Fetches every page of a paginated list endpoint.

        Appends `page={n}` to `path` and concatenates the `content` of
        each page envelope until a page comes back empty or `totalPages`
        is reached. A path that already carries a `page` parameter is
        rejected with `ValueError` rather than sent with two conflicting
        values. A server that keeps returning non-empty pages without
        `totalPages` stops the loop after `_MAX_PAGINATION_PAGES` pages
        with a `ComwattAPIError` instead of hanging forever.

        Args:
            path (str): The endpoint path, optionally with its own query
                parameters (but never a `page` parameter).

        Returns:
            list: The concatenated `content` of all pages.

        """
        if "page" in parse_qs(urlsplit(path).query):
            raise ValueError("path already carries a 'page' parameter")
        separator = "&" if "?" in path else "?"
        items: list[dict[str, Any]] = []
        page = 0
        while True:
            if page >= _MAX_PAGINATION_PAGES:
                raise ComwattAPIError(
                    f"pagination exceeded {_MAX_PAGINATION_PAGES} pages without terminating"
                )
            response = self._request("GET", f"{path}{separator}page={page}").json()
            content = response.get("content", [])
            items.extend(content)
            total_pages = response.get("totalPages")
            if not content:
                break
            if total_pages is not None and page >= total_pages - 1:
                break
            page += 1
        return items

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
