# Comwatt Python Client

## Overview
The Comwatt Python Client is a Python library that provides a convenient way to interact with the Comwatt API. It allows you to authenticate users, retrieve authenticated user information, and access site and device data.

Please note that the Comwatt client is exclusively for gen4 devices: it use `energy.comwatt.com/api`. **Versions below gen4 will not be compatible**. If you're looking for the `go.comwatt.com/api` go to [python-comwatt-client-legacy](https://github.com/MateoGreil/python-comwatt-client-legacy).

## Features
The client currently supports the following methods:

- `authenticate(self, username, password)`: Authenticates a user with the provided username and password. The client re-authenticates automatically on session expiry (HTTP 401) and retries the request once; pass `ComwattClient(auto_reauth=False)` to disable this.
- `is_authenticated(self)`: Returns whether the current session is still valid (probes the API; `True`/`False`, re-raises unexpected errors).
- `logout(self)`: Logs the current session out server-side (`POST /v1/logout`) and clears the stored credentials so `auto_reauth` cannot silently restore the session. Idempotent (a 401 when already logged out is a no-op). Note this is distinct from `close()`, which only releases the local HTTP session without logging out.
- `get_authenticated_user(self)`: Retrieves information about the authenticated user.
- `get_sites(self)`: Retrieves a list of sites associated with the authenticated user.
- `get_site_networks_ts_time_ago(self, site_id, measure_kind = "FLOW", aggregation_level = "NONE", aggregation_type = None, time_ago_unit = "HOUR", time_ago_value = 1, start = None, end = None)`: Retrieves the time series data for the networks of a specific site, based on the provided parameters. **Deprecated** — use `get_site_time_series` instead (emits a `DeprecationWarning`; the endpoint still works but the app has moved to `site-time-series`).
- `get_site_consumption_breakdown_time_ago(self, site_id, aggregation_level = "HOUR", time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)` Retrieves the consumption breakdown data for a specific site, based on the provided parameters. **Deprecated** — use `get_top_consumption` instead (emits a `DeprecationWarning`; the endpoint still works but the app has moved to `top-consumption`).
- `get_devices(self, site_id)`: Retrieves a list of devices for the specified site.
- `get_connected_objects(self, site_id=None, gateway_uid=None)`: Retrieves the connected objects for a site or a gateway. Exactly one of `site_id` / `gateway_uid` is required (raises `ValueError` otherwise).
- `get_connected_object(self, connected_object_id)`: Retrieves information about a specific connected object.
- `get_measure_keys(self, site_id)`: Retrieves the measure keys (flat measurement inventory) for a site — each a `(device, measureKind)` pair with a stable id and `measureKey` UUID.
- `get_tiles(self, site_id)`: Retrieves the dashboard tile configuration for a site (tile type + which device each points at; configuration only, no live values).
- `get_electricity_price(self, site_id)`: Retrieves the EDF Tempo calendar / tariff structure for a site (`tempoSyntheses`, `daily`, ...).
- `get_device_kinds(self, site_uid)`: Retrieves the device-kind catalogue for a site (the "add a device" picker). Takes the short `siteUid` string (from `site["siteUid"]`), not the numeric site id.
- `get_device_ts_time_ago(self, device_id, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = "MAX", time_ago_unit = "DAY", time_ago_value = "1", start = None, end = None)`: Retrieves the time series data for a specific device, based on the provided parameters.
- `get_site_time_series(self, site_id, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = None, time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the whole-site rollup time series data for a specific site, based on the provided parameters.
- `get_top_consumption(self, site_id, aggregation_level = "DAY", time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the per-device consumption breakdown (top 5 devices + "others") for a specific site.
- `get_ecowatt(self)`: Retrieves the RTE EcoWatt grid-stress forecast (array of daily entries with a GREEN/ORANGE/RED status and 24 hourly values). Takes no parameters.
- `switch_capacity(self, capacity_id, enable)`: Turns a switch/relay capacity on or off (`PUT /capacities/{id}/switch`). Takes the numeric capacity `id`.
- `set_pilot_wire(self, capacity_id, state)`: Sets the pilot-wire order of a heating capacity (`PUT /capacities/{id}/pilot-wire`). `state` is passed through as-is; valid values are backend-defined (check the capacity's `selectValues`) and were **not** verified against a live pilot-wire device.
- `set_thermal_mode(self, capacity_id, state)`: Sets the thermal mode of a thermostat capacity, e.g. eco / comfort (`PUT /capacities/{id}/thermal-mode`). Same `state` pass-through caveat as `set_pilot_wire`.
- `set_thermostat_set_point(self, capacity_id, value)`: Sets the target set-point of a thermostat capacity (`PUT /capacities/{id}/thermostat-set-point`). `value` (temperature) is passed through as-is.

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
- `stream_measurements(self, site, *, reconnect=False, reconnect_backoff=1.0, reconnect_backoff_max=60.0, reconnect_max_attempts=None)`: Streams live measurements (`FLOW` / `STATE`) for a single site over STOMP-over-WebSocket. Takes one site dict (as returned by `get_sites`); yields `Measurement` / `CapacityChanged` events. Requires the optional `[stream]` extra (`websocket-client`). Pass `reconnect=True` to enable opt-in exponential-backoff reconnection on socket drops; `reconnect_backoff` sets the initial delay (seconds), `reconnect_backoff_max` caps the delay, and `reconnect_max_attempts` limits consecutive failed connect attempts before raising (`None` = unlimited). Reconnect is off by default; an auth rejection is always terminal.

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

# Get the whole-site rollup time series (productions, consumptions, injections, ...)
site_time_series_data = client.get_site_time_series(sites[0]['id'])
print(site_time_series_data)

# Get the per-device consumption breakdown for a specific site (top 5 + "others")
top_consumption_data = client.get_top_consumption(sites[0]['id'])
print(top_consumption_data)

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

- `ComwattAuthError` — the credentials were rejected (HTTP 401/403 on login) or the session expired (HTTP 401). Re-authenticate.
- `ComwattAPIError` — any other unexpected HTTP status, including non-credential failures of `authenticate()` (e.g. a 5xx during an outage, or a 200 response missing the session cookie). Exposes `.status_code`, `.url`, `.detail`.

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

## Realtime streaming (optional)

For live measurements, install the optional streaming extra (adds `websocket-client`):

```
pip install comwatt-client[stream]
```

Then iterate a single site's measurements as they arrive over STOMP-over-WebSocket:

```python
from comwatt_client import ComwattClient

client = ComwattClient()
client.authenticate("username", "password")

sites = client.get_sites()
for ev in client.stream_measurements(sites[0], reconnect=True):
    print(ev)
```

The generator yields `Measurement` (live `FLOW` / `STATE` values) and `CapacityChanged` (switch/state changes) events. By default (`reconnect=False`) it stops when the WebSocket drops. Pass `reconnect=True` to reconnect automatically with full-jitter exponential backoff:

```python
for ev in client.stream_measurements(
    sites[0],
    reconnect=True,
    reconnect_backoff=1.0,
    reconnect_backoff_max=60.0,
    reconnect_max_attempts=10,
):
    print(ev)
```

The delay between failed connection attempts starts at `reconnect_backoff` seconds and doubles up to `reconnect_backoff_max`. `reconnect_max_attempts` counts **consecutive** failed attempts (resets to zero after any successful connection). An auth rejection (HTTP 401/403) is always terminal and will not be retried. `QUANTITY` measures are emitted only on bucket rollover, so keep a slow REST fallback (e.g. `get_site_time_series`) for absolute totals.

### Mapping streamed measurements to devices

The stream yields measurements keyed by an opaque `capacityId` string. Sensor and switch capacities use `AZUREIOT-co.{N}.instances.{i}.{sensor|switch}.{j}.data`; grid-exchange and battery capacities keep the `sensor.{j}` segment and append the quantity instead — `...sensor.{j}.withdrawal.data`, `...sensor.{j}.injection.data`, `...sensor.{j}.battery_charge.data`, `...sensor.{j}.battery_discharge.data`. To route them to a device and interpret them, join them against `get_connected_objects(site_id)`:

- **`capacityId` ↔ capacity object** — `Measurement.capacity_id` is the `capacityId` string found on each capacity object. That same object also carries `deviceId`, `nature` (e.g. `CLAMP`, `POWER_SENSOR`, `POWER_SWITCH`), `measureKind`, and `production` (bool) — enough to route a measurement to its device and determine its sign with no separate map.
- **Multi-instance / polyphase devices** — a device can expose several `SENSOR` capacities (a 3-phase solar inverter pushes `instances.0`, `instances.1`, `instances.2`). The device's instantaneous power is the **sum** of its `FLOW` capacities, not any single instance. Polyphase capacities carry a `phase` field such as `POSITIVE_1` / `POSITIVE_2` / `POSITIVE_3` (not every capacity has one).
- **Typed value fields** — `Measurement` parses the raw string into `value_float` (when it is numeric — watts for `FLOW`) and `value_bool` (when it is `true`/`false` — on/off for `STATE`). In practice `FLOW` populates `value_float` and `STATE` populates `value_bool`; `Measurement.value` is the raw string the server sent — prefer the typed field.
- **Cadence** — the server pushes measurements in bursts roughly every 15 seconds, grouped per connected object (the `co.{N}` segment of the `capacityId`). It is not a fixed per-device poll: expect a burst of many measures close together, then a gap.
- **Use `get_connected_objects()`, not `get_devices()`, to build the route** — `get_connected_objects(site_id)` returns each connected object (the `co.{N}` segment, via its `coId`) with **all** its capacities, each carrying `capacityId` / `deviceId` / `nature` / `measureKind`. `get_devices()` returns the user-facing device list, but the grid-meter and battery parents come back with empty `features` and `capacities`, so their routable capacities are not exposed there.

  This is the only way to map grid exchange and battery: `...sensor.{j}.withdrawal.data` routes to a `WITHDRAWAL` part-child device, `...sensor.{j}.injection.data` to an `INJECTION` one, `...sensor.{j}.battery_charge.data` to a `BATTERY_CHARGE` device, and `...sensor.{j}.battery_discharge.data` to a `BATTERY_DISCHARGE` device. These are real devices — part-children of the `GRID_METER` / `BATTERY` parent (identified by `deviceKind.code`, not a `nature` field) — that also show up in `get_measure_keys(site_id)`. Some physical clamps on a multi-channel box are present as capacities but have `deviceId: null` until they are assigned to a device — drop those from the route.
- **Switch state** — a device with a `POWER_SWITCH` / `RELAY` capacity receives its on/off state on the stream as `STATE` measurements on a `...switch.N.data` `capacityId`, parallel to the `...sensor.N.data` `FLOW` `capacityId` on the same instance.
- **`CapacityChanged` vs the route** — `CapacityChanged` is also yielded for switch state changes, but its `capacity_id` is the **numeric** capacity `id` (the one `switch_capacity` takes), not the `capacityId` string — don't match it against the string route. Switch changes were not observed during this check (no switch was toggled manually).

Building the `capacityId → (deviceId, nature, production)` route from `get_connected_objects()` (covers every mappable capacity, including grid exchange and battery):

```python
from comwatt_client import ComwattClient, Measurement

client = ComwattClient()
client.authenticate("username", "password")
sites = client.get_sites()

route = {}
for obj in client.get_connected_objects(site_id=sites[0]["id"]):
    for cap in obj["capacities"]:
        device_id = cap["deviceId"]
        if device_id is None:
            continue
        route[cap["capacityId"]] = (device_id, cap["nature"], cap.get("production", False))

for ev in client.stream_measurements(sites[0], reconnect=True):
    if isinstance(ev, Measurement):
        device_id, nature, production = route.get(ev.capacity_id, (None, None, None))
        if device_id is not None:
            print(f"device={device_id} nature={nature} production={production} "
                  f"value={ev.value_float if ev.value_float is not None else ev.value_bool}")
```

## Contributing
Contributions to the Comwatt Python Client are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request on the GitHub repository.
