# Comwatt Python Client

## Overview
The Comwatt Python Client is a Python library that provides a convenient way to interact with the Comwatt API. It allows you to authenticate users, retrieve authenticated user information, and access site and device data.

## Features
The client currently supports the following methods:

- `authenticate(self, username, password)`: Authenticates a user with the provided username and password.
- `get_authenticated_user(self)`: Retrieves information about the authenticated user.
- `get_sites(self)`: Retrieves a list of sites associated with the authenticated user.
- `get_site_networks_ts_time_ago(self, site_id, measure_kind = "VIRTUAL_QUANTITY", aggregation_level = "HOUR", aggregation_type = "SUM", time_ago_unit = "DAY", time_ago_value = 1)`: Retrieves the time series data for the networks of a specific site, based on the provided parameters.
- `get_site_consumption_breakdown_time_ago(self, site_id, aggregation_level = "HOUR", time_ago_unit = "DAY", time_ago_value = 1)` Retrieves the consumption breakdown data for a specific site, based on the provided parameters.
- `get_devices(self, site_id)`: Retrieves a list of devices for the specified site.
- `get_device_ts_time_ago(self, device_id, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = "MAX", time_ago_unit = "DAY", time_ago_value = "1")`: Retrieves the time series data for a specific device, based on the provided parameters.


## Installation
You can install the Comwatt Python Client using pip. Run the following command:

```
pip install comwatt-client
```

## Usage
Here's a simple example of how to use the Comwatt Python Client:

```python
from comwatt.client import ComwattClient

# Create a Comwatt client instance
client = ComwattClient()

# Authenticate the user
client.authenticate('username', 'password')

# Get information about the authenticated user
user_info = client.get_authenticated_user()
print(user_info)

# Get a list of sites associated with the authenticated user
sites = client.get_sites()
print(sites)

# Get time series data for the networks of a specific site
networks_time_series_data = client.get_site_networks_ts_time_ago(sites[0]['id'])
print(networks_time_series_data)

# Get the consumption breakdown data for a specific site, based on the provided parameters.
consumption_breakdown_data = client.get_site_consumption_breakdown_time_ago(sites[0]['id'])
print(consumption_breakdown_data)

# Get a list of devices for a specific site
devices = client.get_devices(sites[0]['id'])
print(devices)

# Get time series data for a specific device
time_series_data = client.get_device_ts_time_ago(devices[0]['id'])
print(time_series_data)
```

Make sure to replace `'username'`, `'password'` with the actual values for your Comwatt account.

## Contributing
Contributions to the Comwatt Python Client are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request on the GitHub repository.
