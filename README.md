# Comwatt Python Client

## Overview
The Comwatt Python Client is a Python library that provides a convenient way to interact with the Comwatt API. It allows you to authenticate users, retrieve authenticated user information, and access site and device data.

Please note that the Comwatt client is exclusively for gen4 devices: it use `energy.comwatt.com/api`. **Versions below gen4 will not be compatible**. If you're looking for the `go.comwatt.com/api` go to [python-comwatt-client-legacy](https://github.com/MateoGreil/python-comwatt-client-legacy).

## Features
The client currently supports the following methods:

- `authenticate(self, username, password)`: Authenticates a user with the provided username and password. The client keeps the session alive automatically: it re-authenticates proactively before a request once the session expiry (`session_expires_at`) is within 30 s, and falls back to re-authenticating on a 401 response, retrying the request once; pass `ComwattClient(auto_reauth=False)` to disable both.
- `is_authenticated(self)`: Returns whether the current session is still valid (probes the API; `True`/`False`, re-raises unexpected errors).
- `session_expires_at`: Property — the instant the current session cookie dies, as a UTC-aware `datetime` (captured from the login response's `x-cwt-token` header; login time + 2 h). Refreshed on every (re-)authentication, reset to `None` on `logout()`; `None` before the first login or if the server omits the header.
- `logout(self)`: Issues `POST /v1/logout`, which expires the `cwt_session` cookie client-side (Set-Cookie 1970) and drops it from the local jar — but does **not** invalidate the session server-side (live-verified: the old cookie keeps working until its natural expiry, ~login + 2 h). Also clears the stored credentials so `auto_reauth` cannot silently restore the session. Idempotent (a 401 when already logged out is a no-op). Note this is distinct from `close()`, which only releases the local HTTP session without logging out.
- `get_authenticated_user(self)`: Retrieves information about the authenticated user.
- `get_sites(self)`: Retrieves a list of sites associated with the authenticated user.
- `get_site(self, site_id)`: Retrieves a single site. Takes the **numeric site id** (from `site["id"]`), not the short `siteUid` string.
- `get_site_by_uid(self, site_uid)`: Retrieves a single site. Takes the short `siteUid` string (from `site["siteUid"]`), not the numeric site id.
- `get_site_networks_ts_time_ago(self, site_id, measure_kind = "FLOW", aggregation_level = "NONE", aggregation_type = None, time_ago_unit = "HOUR", time_ago_value = 1, start = None, end = None)`: Retrieves the time series data for the networks of a specific site, based on the provided parameters. **Deprecated** — use `get_site_time_series` instead (emits a `DeprecationWarning`; the endpoint still works but the app has moved to `site-time-series`).
- `get_site_consumption_breakdown_time_ago(self, site_id, aggregation_level = "HOUR", time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)` Retrieves the consumption breakdown data for a specific site, based on the provided parameters. **Deprecated** — use `get_top_consumption` instead (emits a `DeprecationWarning`; the endpoint still works but the app has moved to `top-consumption`).
- `get_devices(self, site_id)`: Retrieves a list of devices for the specified site.
- `get_connected_objects(self, site_id=None, gateway_uid=None)`: Retrieves the connected objects for a site or a gateway. Exactly one of `site_id` / `gateway_uid` is required (raises `ValueError` otherwise).
- `get_connected_object(self, connected_object_id)`: Retrieves information about a specific connected object.
- `get_connected_object_devices(self, connected_object_id)`: Retrieves the devices exposed by a specific connected object (`GET /connectedobjects/{id}/devices`) — narrower than `get_devices(site_id)`. Full device documents (`capacities`, `deviceKind`, `site`, `uuid`, ...; live-verified 2026-10-27).
- `get_gateway(self, gateway_id)`: Retrieves a gateway (the Comwatt box) by its **numeric id** (`gateway["id"]`) — the `gatewayUid` string is rejected with 400. Returns the full gateway document (JSON-with-refs, returned as-is); `connected` / `updating` / `status` are the "box offline / being updated" flags.
- `get_gateway_by_uid(self, gateway_uid)`: Retrieves a gateway by its opaque `gatewayUid` string. Returns the same document as `get_gateway`.
- `get_gateway_network(self, gateway_uid)`: Retrieves the network details of a gateway (signal strength, channel, ...). ⚠ Takes the **`gatewayUid`**, not the numeric id — the numeric id answers 412 `gateway.not.found.for.fetching.network.details` (bare JSON array error body).
- `get_gateway_ssids(self, gateway_id)`: Retrieves the Wi-Fi networks visible to a gateway, by **numeric id**. ⚠ Privacy-sensitive: the response includes **neighbouring** Wi-Fi networks, not just the gateway's own.
- `get_measure_keys(self, site_id)`: Retrieves the measure keys (flat measurement inventory) for a site — each a `(device, measureKind)` pair with a stable id and `measureKey` UUID.
- `get_tiles(self, site_id)`: Retrieves the dashboard tile configuration for a site (tile type + which device each points at; configuration only, no live values).
- `get_electricity_price(self, site_id)`: Retrieves the EDF Tempo calendar / tariff structure for a site (`tempoSyntheses`, `daily`, ...).
- `get_device_kinds(self, site_uid)`: Retrieves the device-kind catalogue for a site (the "add a device" picker). Takes the short `siteUid` string (from `site["siteUid"]`), not the numeric site id.
- `get_products(self)`: Retrieves the Comwatt hardware catalogue (`MONITOR_GEN_4`, `POWER_GEN_4`, ...; `{id, name, brand, cardinality, features}`).
- `get_product(self, product_id)`: Retrieves a single catalogue product by its numeric id — same shape as the `get_products()` entries.
- `get_timezones(self)`: Retrieves the static timezone list (`{timeZone, posix}` pairs: IANA name + POSIX TZ string).
- `get_modbus_configurations(self)`: Retrieves the Modbus configuration catalogue (one entry per supported Modbus device family: `{id, name, label, port, slave, device_kinds}` — note `device_kinds` is snake_case). Modbus pairing itself is an installer flow and is not exposed.
- `get_plannings(self, site_id)`: Retrieves the plannings (schedules) for a site. Auto-paginates through the `content`/`totalPages` envelope and returns a flat list. The server currently ignores `siteId` (returns the authenticated user's plannings); the trailing-slash variant 404s, and the `?deviceId=` variant is deliberately not offered.
- `update_planning(self, planning_id, payload)`: Updates a planning via `PUT /plannings/{planning_id}` with the payload sent as-is. Second-hand pitfalls (not live-tested): the inline `device` object must carry `"@class": "Device"` plus a numeric `id` (else 400 "Failed to read request"), each schedule's `typicalDay` must be a full inline object (id-only → 500), and the PUT replaces `typicalDaySchedules` wholesale — include every surviving schedule and re-read after writing; `optimalPlanning: true` schedules are server-managed and not writable.
- `get_typical_days(self, site_id)`: Retrieves the "typical day" templates for a site (`ON` / `OFF` / `COMWATT` time ranges driving the auto-consumption optimizer). Auto-paginates and returns a flat list.
- `create_typical_day(self, site_id, payload)`: Creates a "typical day" template for a site (`POST /api/typicaldays?siteId=`). ⚠ `siteId` goes in the **query string**, not the body — second-hand from the solareco reverse-engineering, not live-tested. The payload is passed through unvalidated: build it from `get_typical_days` output; the response shape is not live-verified.
- `update_typical_day(self, typical_day_id, payload)`: Updates an existing "typical day" template (`PUT /api/typicaldays/{id}`). The payload is passed through unvalidated — build it from `get_typical_days` output; the response shape is not live-verified.
- `get_alert_configs(self, device_id)`: Retrieves the alert config (consumption threshold) of a device (`GET /alertconfigs/v2?deviceId=`). Returns a single `{period, id, min, max, activated, deviceId}` object; devices without a configured alert answer 200 with a skeleton object (`id`/`min`/`max`/`deviceId` null, `activated` false) instead of 404. `min` and `max` are independently nullable; observed `period`: `SLIDING_24_HOURS`. `device_id` is mandatory server-side (bare GET → 400).
- `set_alert_config(self, device_id, min, max, period = "SLIDING_24_HOURS", activated = True)`: Sets the alert config (consumption threshold) of a device. Two-step flow: resolves the numeric config id via `get_alert_configs`, then sends `PUT /alertconfigs/v2/{id}` with `{deviceId, min, max, period, activated}`. Write body shape bundle-derived, not live-verified. Raises `ComwattAPIError` when the device has no configured alert (skeleton `id` null) — the creation path (POST) is not exposed. The `min`/`max` parameter names shadow the builtins to mirror the API body fields.
- `get_thermal_control(self, device_id)`: Retrieves the thermal-control configuration (set-point / mode) of a device (`GET /thermalcontrol?deviceId=`). Returns `None` when the API answers 200 with an empty body (non-thermal devices). The payload shape is unverified — no thermal/SG-Ready equipment on the probe site, so the keys are presumed rather than observed.
- `set_thermal_control(self, thermal_control_id, device_id, set_point = None, mode = None)`: Updates the thermal-control configuration (set-point / mode) of a device (`PUT /thermalcontrol/{id}`). `thermal_control_id` is the thermal-control **config** id (a device id 404s), obtained from `get_thermal_control(device_id)`; validation runs before the path lookup. The body's inline `device` object is the only required field and must carry the Jackson discriminator `"@class": "Device"` + the numeric id (else 400 "Failed to read request"); `set_point` / `mode` are optional and only sent when not `None`. Success path unverified (no thermal-control config on the probe account); `mode` values unconfirmed at this endpoint (capacity-level thermal-mode enum: OFF/HEAT/COOL).
- `get_device_ts_time_ago(self, device_id, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = "MAX", time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the time series data for a specific device, based on the provided parameters.
- `get_site_time_series(self, site_id, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = None, time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the whole-site rollup time series data for a specific site, based on the provided parameters.
- `get_site_network_time_series(self, site_id, site_network_type, measure_kind = "FLOW", aggregation_level = "HOUR", aggregation_type = None, time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the time series of one of a site's virtual networks — `PRODUCTION` / `CONSUMPTION` / `INJECTION` / `WITHDRAWAL` / `CHARGE` / `DISCHARGE` (battery flows via the directional `CHARGE` / `DISCHARGE`; `BATTERY` and `GRID` are rejected with 400). Site-addressed `siteNetworkType` overload of the device `time-series` endpoint.
- `get_devices_ts_time_ago(self, device_ids, *, max_workers = None, **kwargs)`: Fans `get_device_ts_time_ago` out over a `concurrent.futures.ThreadPoolExecutor` (one call per device, default `max_workers = min(8, len(device_ids))`). Results are returned in `device_ids` order; `**kwargs` are forwarded to every call. If one or more devices fail, all calls are still awaited and the first failure in `device_ids` order is raised. Returns `[]` for an empty `device_ids` without starting any threads.
- `get_top_consumption(self, site_id, aggregation_level = "DAY", time_ago_unit = "DAY", time_ago_value = 1, start = None, end = None)`: Retrieves the per-device consumption breakdown (top 5 devices + "others") for a specific site.
- `get_ecowatt(self)`: Retrieves the RTE EcoWatt grid-stress forecast (array of daily entries with a GREEN/ORANGE/RED status and 24 hourly values). Takes no parameters.
- `client.weather.forecast(*, city=None, zip=None, country='FR', units='metric', lang='fr')`: Retrieves the OpenWeatherMap 5-day/3-hour forecast through the unauthenticated same-origin weather proxy (no `authenticate()` needed). Exactly one of `city` / `zip` (raises `ValueError` otherwise). Returns the raw OWM payload (`cnt=40` entries + `city` block). Note it lives outside `/api`.
- `switch_capacity(self, capacity_id, enable)`: Turns a switch/relay capacity on or off (`PUT /capacities/{id}/switch`). Takes the numeric capacity `id`.
- `set_pilot_wire(self, capacity_id, state)`: Sets the pilot-wire order of a heating capacity (`PUT /capacities/{id}/pilot-wire`). Requires a "select" capacity (else 412 `capacity.is.not.a.select`). `state` is **not** server-side enum-bound — the 2026-10-27 binding sweep passed any string — so valid orders remain unverified (no pilot-wire hardware on the probe account); check the capacity's `selectValues`.
- `set_thermal_mode(self, capacity_id, state)`: Sets the thermal mode of a thermostat capacity to `OFF`, `HEAT` or `COOL` (`PUT /capacities/{id}/thermal-mode`). `state` is server-side enum-bound (live-pinned 2026-10-27 by a sweep of 42 candidates): any other value is rejected with 400 "Failed to convert 'state'". Requires a "select" capacity (else 412 `capacity.is.not.a.select`); check the capacity's `selectValues` for the values valid on your hardware.
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
- `get_device_capacities(self, device_id)`: Retrieves the capacities of a specific device as full objects (no `@ref` indirection, unlike the site-wide listing). Each capacity has two ids: the numeric `id` (expected by `switch_capacity` / `set_pilot_wire` / ...) and the opaque `capacityId` string (echoed in WebSocket frames).
- `put_device(self, device_id, payload)`: Updates a specific device with the provided payload.
- `set_device_mode(self, device_id, mode)`: Sets the control mode of a specific device (`PUT /devices/{id}/mode`) — the "Off / On / Auto" control: `ON` / `OFF` / `COMWATT` (`COMWATT` = solar-driven auto, same family as the planning modes). The mode is sent as a JSON body `{"mode": mode}` (bundle-derived and not live-verified; if the API answers 400, it may instead expect a query parameter). Mode values were observed read-only in typical-day / planning modes; no write-based enum validation was performed.
- `stream_measurements(self, site, *, reconnect=False, reconnect_backoff=1.0, reconnect_backoff_max=60.0, reconnect_max_attempts=None)`: Streams live measurements (`FLOW` / `STATE`) for a single site over STOMP-over-WebSocket. Takes one site dict (as returned by `get_sites`); yields `Measurement` / `CapacityChanged` events. Requires the optional `[stream]` extra (`websocket-client`). Pass `reconnect=True` to enable opt-in exponential-backoff reconnection on socket drops; `reconnect_backoff` sets the initial delay (seconds), `reconnect_backoff_max` caps the delay, and `reconnect_max_attempts` limits consecutive failed connect attempts before raising (`None` = unlimited). Reconnect is off by default; an auth rejection is always terminal. The server declines STOMP heart-beats, so the client sends the raw `__ping__` text as a keep-alive every 60 s (mirroring the SPA); silent-socket timeouts no longer end the stream. Teardown (generator exhaustion, `close()`, or socket death) best-effort SENDs `/app/streaming/stop` before the STOMP DISCONNECT, mirroring the SPA. Before each WebSocket handshake (initial and reconnect), the client proactively refreshes the session when it is within 30 s of expiry (`auto_reauth` + stored credentials); a handshake 401 still falls back to reactive re-auth.

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

# Set the control mode of a specific device to MANUAL
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

  `detail` is extracted from the API's two error body shapes: the RFC-7807 `detail` field, and — for the bare JSON array of Spring validation errors some endpoints return instead (e.g. `412`, also seen on `404`/`403`) — each entry's `code` (falling back to `codes[0]`, then `defaultMessage`), comma-joined.

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

## Architecture

`ComwattClient` composes one mixin per API domain (auth, sites, devices, gateways, ...), each contributing its `get_*` / `set_*` methods flat on the client instance. The single exception is `client.weather`, a namespaced proxy.

The rule deciding the split:

> A domain gets a namespaced proxy if and only if its transport differs from the authenticated REST path — a different base URL/host, protocol, or auth model. Method count is never a trigger.

- **Weather** is a proxy because it hits an unauthenticated OpenWeatherMap forecast proxy outside `/api`, while reusing the client's HTTP session.
- **Streaming** is transport-divergent too (WebSocket, different host) but stays a flat method (`stream_measurements`): it is authenticated and session-coupled. It becomes a proxy only if a second streaming method ever lands.

## Related projects

Actively maintained projects worth knowing about. This is deliberately not an
inventory of everything Comwatt-related on GitHub — most of it is abandoned or
pre-gen4, and pointing you at a dead scraper would be worse than saying nothing.

- [homeassistant-comwatt](https://github.com/MateoGreil/homeassistant-comwatt) — Home Assistant integration built on this library (gen 4). If domotics is your goal, install this via HACS rather than wiring the client up yourself.
- [comwatt_indepbox](https://github.com/ZoomeoTooknor/comwatt_indepbox) — Home Assistant integration for pre-gen4 boxes (`go.comwatt.com`). Useful if you landed here with older hardware and want a working integration rather than a Python library.
- [solareco](https://github.com/paulthvt/solareco) — Kotlin Multiplatform app (Android / desktop) with its own gen-4 client. The only other actively maintained implementation, and a handy second opinion when an undocumented endpoint changes behaviour.

## API field notes

The API this client talks to is private and undocumented, so
[`docs/energy.comwatt.com/`](docs/energy.comwatt.com/) collects
reverse-engineered notes on it: authentication, the aggregation/time-series
endpoints, capacities, the STOMP-over-WebSocket stream, and the gotchas that
bite implementors (two ids per site, `@ref` graphs, mandatory
`aggregationLevel`, ...). They are best-effort and dated — verify anything
load-bearing against the live API.

## Contributing
Contributions to the Comwatt Python Client are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request on the GitHub repository.
