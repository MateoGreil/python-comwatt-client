# Comwatt Python Client

## Overview
The Comwatt Python Client is a Python library that provides a convenient way to interact with the Comwatt API. It allows you to authenticate users, retrieve authenticated user information, and access site and device data.

Please note that the Comwatt client is exclusively for gen4 devices: it use `energy.comwatt.com/api`. **Versions below gen4 will not be compatible**. If you're looking for the `go.comwatt.com/api` go to [python-comwatt-client-legacy](https://github.com/MateoGreil/python-comwatt-client-legacy).

## Features
The client currently supports the following methods:

- `authenticate(self, username, password)`: Authenticates a user with the provided username and password. The client re-authenticates automatically on session expiry (HTTP 401) and retries the request once; pass `ComwattClient(auto_reauth=False)` to disable this.
- `is_authenticated(self)`: Returns whether the current session is still valid (probes the API; `True`/`False`, re-raises unexpected errors).
- `get_authenticated_user(self)`: Retrieves information about the authenticated user.
- `get_sites(self)`: Retrieves a list of sites associated with the authenticated user.
- `get_site_networks_ts_time_ago(self, site_id, measure_kind = "FLOW", aggregation_level = "NONE", aggregation_type = None, time_ago_unit = "HOUR", time_ago_value = 1, start = None, end = None)`: Retrieves the time series data for the networks of a specific site, based on the provided parameters.
- `get_site_consumption_breakdown_time_ago(self, site_id, aggregation_level = "HOUR", time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)` Retrieves the consumption breakdown data for a specific site, based on the provided parameters.
- `get_devices(self, site_id)`: Retrieves a list of devices for the specified site.
- `get_connected_objects(self, site_id=None, gateway_uid=None)`: Retrieves the connected objects for a site or a gateway. Exactly one of `site_id` / `gateway_uid` is required (raises `ValueError` otherwise).
- `get_connected_object(self, connected_object_id)`: Retrieves information about a specific connected object.
- `get_measure_keys(self, site_id)`: Retrieves the measure keys (flat measurement inventory) for a site — each a `(device, measureKind)` pair with a stable id and `measureKey` UUID.
- `get_device_ts_time_ago(self, device_id, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = "MAX", time_ago_unit = "DAY", time_ago_value = "1", start = None, end = None)`: Retrieves the time series data for a specific device, based on the provided parameters.
- `get_site_time_series(self, site_id, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = None, time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the whole-site rollup time series data for a specific site, based on the provided parameters.
- `get_top_consumption(self, site_id, aggregation_level = "DAY", time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the per-device consumption breakdown (top 5 devices + "others") for a specific site.

`start`/`end` accept a `datetime` or ISO-8601 string and select an absolute window instead of the relative `time_ago_*` params; a naive `datetime` is treated as UTC:

```python
from datetime import datetime

client.get_device_ts_time_ago(
    "device-1",
    start=datetime(2026, 7, 4, 0, 0, 0),
    end=datetime(2026, 7, 5, 0, 0, 0),
)
```
- `get_device(self, device_id)`: Retrieves information about a specific device.
- `put_device(self, device_id, payload)`: Updates a specific device with the provided payload.

## Installation
You can install the Comwatt Python Client using pip. Run the following command:

```
pip install comwatt-client
```

## Usage
Here's a simple example of how to use the Comwatt Python Client:

```python
from comwatt_client import ComwattClient

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

# Set the control mode of a specific device to MANUL
device = client.get_device(devices[0]['id'])
device['configuration']['controlMode'] = 'MANUAL'
client.put_device(device['id'], device)

# Switch the POWER_SWITCH capacity
for feature in device['features']:
    for capacity in feature['capacities']:
        if capacity.get('capacity', {}).get('nature') == "POWER_SWITCH":
            capacity_id = capacity['capacity']['id']
client.switch_capacity(capacity_id, False)
client.switch_capacity(capacity_id, True)

```

Make sure to replace `'username'`, `'password'` with the actual values for your Comwatt account.

## Error handling

All errors raised by the client subclass `ComwattError`:

- `ComwattAuthError` — login failed or the session expired (HTTP 401). Re-authenticate.
- `ComwattAPIError` — any other unexpected HTTP status. Exposes `.status_code`, `.url`, `.detail`.

```python
from comwatt_client import ComwattClient, ComwattAuthError, ComwattAPIError

client = ComwattClient()
try:
    client.authenticate("username", "password")
    sites = client.get_sites()
except ComwattAuthError:
    ...  # credentials wrong or session expired — re-authenticate
except ComwattAPIError as e:
    print(e.status_code, e.url, e.detail)
```

## Contributing
Contributions to the Comwatt Python Client are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request on the GitHub repository.
