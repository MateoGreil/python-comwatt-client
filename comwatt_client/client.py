import requests
import json
import hashlib

class ComwattClient:
    """
    A client for interacting with the Comwatt API.

    Args:
        None

    Attributes:
        base_url (str): The base URL of the Comwatt API.
        session (requests.Session): The session object for making HTTP requests.

    """
    def __init__(self):
        self.base_url = 'https://energy.comwatt.com/api'
        self.session = requests.Session()

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

        response = self.session.post(url, json=data)

        if response.status_code != 200:
            raise Exception(f'Authentication failed: {response.status_code}')

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

        url = f'{self.base_url}/users/authenticated'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving authenticated user: {response.status_code}')

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

        url = f'{self.base_url}/sites'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving sites: {response.status_code}')


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
            measure_kind (str): The kind of measure (default: "VIRTUAL_QUANTITY").
            aggregation_level (str): The aggregation level (default: "HOUR").
            aggregation_type (str): The aggregation type (default: None, can be : None, "SUM", "MAX").
            time_ago_unit (str): The unit of time ago (default: "DAY").
            time_ago_value (int): The value of time ago (default: 1).

        Returns:
            dict: The time series data.

        Raises:
            Exception: If an error occurs while retrieving the data.

        """

        url = (f'{self.base_url}/aggregations/site-networks-ts-time-ago?'
               f'siteId={site_id}&'
               f'measureKind={measure_kind}&'
               f'aggregationLevel={aggregation_level}&'
               f'timeAgoUnit={time_ago_unit}&'
               f'timeAgoValue={time_ago_value}')

        if aggregation_type != None:
            url += f'&aggregationType={aggregation_type}'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving aggregations: {response.status_code}')

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

        url = (f'{self.base_url}/aggregations/consumption-breakdown-time-ago?'
                f'siteId={site_id}&'
                f'aggregationLevel={aggregation_level}&'
                f'timeAgoUnit={time_ago_unit}&'
                f'timeAgoValue={time_ago_value}')

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving aggregations: {response.status_code}')

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

        url = f'{self.base_url}/devices?siteId={site_id}'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving sites: {response.status_code}')

    def get_device(self, device_id):
        """
        Retrieves information about a specific device.

        Args:
            device_id (str): The ID of the device.

        Returns:
            dict: A dictionary containing the device information.

        """
        url = f'{self.base_url}/devices/{device_id}'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving device {device_id}: {response.status_code}')

    def put_device(self, device_id, payload):
        """
        Updates a specific device with the provided payload.

        Args:
            device_id (str): The ID of the device.
            payload (dict): The payload to update the device.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        url = f'{self.base_url}/devices/{device_id}'

        response = self.session.put(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving sites: {response.status_code}')


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

        url = (f'{self.base_url}/aggregations/time-series?'
               f'id={device_id}&'
               f'measureKind={measure_kind}&'
               f'aggregationLevel={aggregation_level}&'
               f'aggregationType={aggregation_type}&'
               f'timeAgoUnit={time_ago_unit}&'
               f'timeAgoValue={time_ago_value}')

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving aggregations: {response.status_code} for url {url}')

    def switch_capacity(self, capacity_id, enable):
        """
        Switch a specific capcaity to the enable value.

        Args:
            capacity_id (str): The ID of the capacity.
            enable (bool): The target state.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        url = f'{self.base_url}/capacities/{capacity_id}/switch?enable={enable}'

        response = self.session.put(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving sites: {response.status_code}')
