from __future__ import annotations

import requests
import json
import hashlib

from types import TracebackType
from typing import Any, TYPE_CHECKING

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


class ComwattClient:
    """
    A client for interacting with the Comwatt API.

    Args:
        None

    Attributes:
        base_url (str): The base URL of the Comwatt API.
        session (requests.Session): The session object for making HTTP requests.

    """
    def __init__(self, timeout: float = 30, auto_reauth: bool = True) -> None:
        self.base_url = 'https://energy.comwatt.com/api'
        self.session = requests.Session()
        self.timeout = timeout
        self.auto_reauth = auto_reauth
        self._username: str | None = None
        self._auth_hash: str | None = None

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(f'jbjaonfusor_{password}_4acuttbuik9'.encode()).hexdigest()

    def _post_authent(self, username: str, password_hash: str) -> None:
        url = f'{self.base_url}/v1/authent'
        data = {'username': username, 'password': password_hash}

        response = self.session.post(url, json=data, timeout=self.timeout)

        if response.status_code != 200:
            detail = _response_detail(response)
            raise ComwattAuthError(status_code=response.status_code, url=response.url, detail=detail, response=response)

        if not self.session.cookies.get("cwt_session"):
            raise ComwattAuthError("Authentication succeeded (HTTP 200) but no cwt_session cookie was set")

    def authenticate(self, username: str, password: str) -> None:
        """
        Authenticates a user with the provided username and password.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            None

        Raises:
            Exception: If the authentication fails.

        """

        password_hash = self._hash_password(password)
        self._post_authent(username, password_hash)

        self._username = username
        self._auth_hash = password_hash

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

    def is_authenticated(self) -> bool:
        """
        Checks whether the current session cookie is still accepted by the API.

        Args:
            None

        Returns:
            bool: True if the session is authenticated, False if the API
                rejected it (401/403).

        Raises:
            Exception: If an unexpected error occurs while probing the API.

        """

        url = f'{self.base_url}/users/authenticated'

        response = self.session.get(url, timeout=self.timeout)
        if response.status_code == 200:
            return True
        elif response.status_code in (401, 403):
            return False
        else:
            raise _api_error(response)

    def get_authenticated_user(self) -> dict[str, Any]:
        """
        Retrieves information about the authenticated user.

        Args:
            None

        Returns:
            dict: Information about the authenticated user.

        Raises:
            Exception: If an error occurs while retrieving the information.

        """

        return self._request("GET", "/users/authenticated").json()

    def get_sites(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of sites associated with the authenticated user.

        Args:
            None

        Returns:
            list: A list of sites.

        Raises:
            Exception: If an error occurs while retrieving the sites.

        """

        return self._request("GET", "/sites").json()


    def get_site_networks_ts_time_ago(self, site_id: int | str,
            measure_kind: str = "FLOW",
            aggregation_level: str = "NONE",
            aggregation_type: str | None = None,
            time_ago_unit: str = "HOUR",
            time_ago_value: int | str = 1) -> dict[str, Any]:
        """
        Retrieves the time series data for the networks of a specific site, based on the provided parameters.

        Args:
            site_id (str): The ID of the site.
            measure_kind (str): The kind of measure (default: "FLOW").
            aggregation_level (str): The aggregation level (default: "NONE").
            aggregation_type (str): The aggregation type (default: None, can be : None, "SUM", "MAX").
            time_ago_unit (str): The unit of time ago (default: "HOUR").
            time_ago_value (int): The value of time ago (default: 1).

        Returns:
            dict: The time series data.

        Raises:
            Exception: If an error occurs while retrieving the data.

        """

        path = (f'/aggregations/site-networks-ts-time-ago?'
               f'siteId={site_id}&'
               f'measureKind={measure_kind}&'
               f'aggregationLevel={aggregation_level}&'
               f'timeAgoUnit={time_ago_unit}&'
               f'timeAgoValue={time_ago_value}')

        if aggregation_type != None:
            path += f'&aggregationType={aggregation_type}'

        return self._request("GET", path).json()

    def get_site_consumption_breakdown_time_ago(self, site_id: int | str,
            aggregation_level: str = "HOUR",
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = 1) -> dict[str, Any]:
        """
        Retrieves the consumption breakdown data for a specific site, based on the provided parameters.

        Args:
            site_id (str): The ID of the site.
            aggregation_level (str): The aggregation level (default: "HOUR").
            time_ago_unit (str): The unit of time ago (default: "DAY").
            time_ago_value (int): The value of time ago (default: 1).

        Returns:
            dict: The consumption breakdown data.

        Raises:
            Exception: If an error occurs while retrieving the data.

        """

        path = (f'/aggregations/consumption-breakdown-time-ago?'
                f'siteId={site_id}&'
                f'aggregationLevel={aggregation_level}&'
                f'timeAgoUnit={time_ago_unit}&'
                f'timeAgoValue={time_ago_value}')

        return self._request("GET", path).json()

    def get_devices(self, site_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves a list of devices for the specified site.

        Args:
            site_id (str): The ID of the site.

        Returns:
            list: A list of devices.

        Raises:
            Exception: If an error occurs while retrieving the devices.

        """

        return self._request("GET", f"/devices?siteId={site_id}").json()

    def get_device(self, device_id: int | str) -> dict[str, Any]:
        """
        Retrieves information about a specific device.

        Args:
            device_id (str): The ID of the device.

        Returns:
            dict: A dictionary containing the device information.

        """
        return self._request("GET", f"/devices/{device_id}").json()

    def put_device(self, device_id: int | str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Updates a specific device with the provided payload.

        Args:
            device_id (str): The ID of the device.
            payload (dict): The payload to update the device.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request("PUT", f"/devices/{device_id}", json=payload).json()


    def get_device_ts_time_ago(self, device_id: int | str,
            measure_kind: str = "FLOW",
            aggregation_level: str = "HOUR",
            aggregation_type: str = "MAX",
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = "1") -> dict[str, Any]:
        """
        Retrieves the time series data for a specific device, based on the provided parameters.

        Args:
            device_id (str): The ID of the device.
            measure_kind (str): The kind of measure (default: "FLOW").
            aggregation_level (str): The aggregation level (default: "HOUR").
            aggregation_type (str): The aggregation type (default: "MAX").
            time_ago_unit (str): The unit of time ago (default: "DAY").
            time_ago_value (str): The value of time ago (default: "1").

        Returns:
            dict: The time series data.

        Raises:
            Exception: If an error occurs while retrieving the data.

        """

        path = (f'/aggregations/time-series?'
               f'id={device_id}&'
               f'measureKind={measure_kind}&'
               f'aggregationLevel={aggregation_level}&'
               f'aggregationType={aggregation_type}&'
               f'timeAgoUnit={time_ago_unit}&'
               f'timeAgoValue={time_ago_value}')

        return self._request("GET", path).json()

    def switch_capacity(self, capacity_id: int | str, enable: bool) -> dict[str, Any]:
        """
        Switch a specific capcaity to the enable value.

        Args:
            capacity_id (str): The ID of the capacity.
            enable (bool): The target state.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request("PUT", f"/capacities/{capacity_id}/switch?enable={str(enable).lower()}").json()

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

    def __enter__(self) -> ComwattClient:
        """
        Enters the runtime context for this client.

        Args:
            None

        Returns:
            ComwattClient: This client instance.

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
