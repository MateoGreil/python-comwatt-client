import requests
import json
import hashlib

from .exceptions import ComwattAPIError, ComwattAuthError


def _response_detail(response):
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        return body.get("detail")
    return None


def _api_error(response):
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
    def __init__(self, timeout=30):
        self.base_url = 'https://energy.comwatt.com/api'
        self.session = requests.Session()
        self.timeout = timeout

    def authenticate(self, username, password):
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

        url = f'{self.base_url}/v1/authent'
        encoded_password = hashlib.sha256(f'jbjaonfusor_{password}_4acuttbuik9'.encode()).hexdigest()
        data = {'username': username, 'password': encoded_password}

        response = self.session.post(url, json=data, timeout=self.timeout)

        if response.status_code != 200:
            detail = _response_detail(response)
            raise ComwattAuthError(status_code=response.status_code, url=response.url, detail=detail, response=response)

        if not self.session.cookies.get("cwt_session"):
            raise ComwattAuthError("Authentication succeeded (HTTP 200) but no cwt_session cookie was set")

    def _request(self, method, path, **kwargs):
        url = f'{self.base_url}{path}'
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if response.status_code == 200:
            return response
        else:
            raise _api_error(response)

    def is_authenticated(self):
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

    def get_authenticated_user(self):
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

    def get_sites(self):
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


    def get_site_networks_ts_time_ago(self, site_id,
            measure_kind = "FLOW",
            aggregation_level = "NONE",
            aggregation_type = None,
            time_ago_unit = "HOUR",
            time_ago_value = 1):
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

    def get_site_consumption_breakdown_time_ago(self, site_id,
            aggregation_level = "HOUR",
            time_ago_unit = "DAY",
            time_ago_value = 1):
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

    def get_devices(self, site_id):
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

    def get_device(self, device_id):
        """
        Retrieves information about a specific device.

        Args:
            device_id (str): The ID of the device.

        Returns:
            dict: A dictionary containing the device information.

        """
        return self._request("GET", f"/devices/{device_id}").json()

    def put_device(self, device_id, payload):
        """
        Updates a specific device with the provided payload.

        Args:
            device_id (str): The ID of the device.
            payload (dict): The payload to update the device.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request("PUT", f"/devices/{device_id}", json=payload).json()


    def get_device_ts_time_ago(self, device_id,
            measure_kind = "FLOW",
            aggregation_level = "HOUR",
            aggregation_type = "MAX",
            time_ago_unit = "DAY",
            time_ago_value = "1"):
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

    def switch_capacity(self, capacity_id, enable):
        """
        Switch a specific capcaity to the enable value.

        Args:
            capacity_id (str): The ID of the capacity.
            enable (bool): The target state.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request("PUT", f"/capacities/{capacity_id}/switch?enable={str(enable).lower()}").json()
