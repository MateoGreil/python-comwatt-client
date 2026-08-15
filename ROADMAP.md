# Roadmap

Backlog for this repo — the field notes in [`docs/energy.comwatt.com/`](docs/energy.comwatt.com/)
and the `comwatt_client` package.

Everything below comes from a live re-exploration of the (undocumented)
`energy.comwatt.com` API on **2026-08-15**, probing as a normal `END_USER`
against SPA bundle `main.5d426c11.js`. Each item carries the facts needed to
act on it, so no external notes are required.

Reminder: there is still **no official API, OpenAPI schema or developer
portal** (`api.`/`developers.`/`dev.`/`partners.comwatt.com` do not even
resolve), so every claim here is reverse-engineered and should be re-checked
against the live API before being relied upon.

## 1. Field-notes corrections (verified wrong or stale)

- [ ] **`aggregationLevel` does not accept `WEEK`.** Live: `400 Failed to convert 'aggregationLevel' with value: 'WEEK'` on all three aggregation endpoints. Real set: `NONE`, `HOUR`, `DAY`, `MONTH`, `YEAR`. → `aggregations.md` (l.59) and the `get_*_time_series` docstrings.
- [ ] **`GET /api/plannings?deviceId={id}` returns `500 Internal error`** (server-side bug, reproduced on 5 devices of different kinds). The per-device planning view is unusable; use the site-wide variant. → `misc-endpoints.md`.
- [ ] **`/api/plannings/?siteId=…` 404 is caused by the trailing slash**, not by an empty result set (`No static resource api/plannings.`). Without the slash, `GET /api/plannings?siteId={siteId}` → `200` paginated. Our "Spring returns 404 on empty lists" gotcha is a misdiagnosis and should be dropped from `README.md` too.
- [ ] **`GET /api/gateways/by-gateway-uid/{uid}` is no longer 403 for `END_USER`** — it returns `200`, as do `/api/gateways/{id}` and `/api/gateways/{id}/with-sales-company`. → `devices.md` (l.134).
- [ ] **`GET /api/gateways/{gatewayId}/diagnostic` does not exist** (`404 No static resource`, and no such call in the bundle). Remove it. → `devices.md`.
- [ ] **`/api/electricitycontract/{id}`: the TODO is resolved.** The path param is the **site id**, the response is a **JSON array** (`[]` when the site has no contract), and no query param is involved. → `misc-endpoints.md`.
- [ ] **`/api/gateways/{…}/network` and `/ssids` take different ids** — a third instance of the "two ids" trap: `/ssids` needs the **numeric id** (a uid gives `400 Failed to convert 'gatewayId'`), while `/network` and `scan-modbus-ip` need the **`gatewayUid`** (a numeric id gives `412 gateway.not.found.for.fetching.network.details`). → `devices.md` + the gotchas list in `README.md`.

## 2. Field-notes additions

### 2.1 Non-`/api` proxies (new page or a section in `misc-endpoints.md`)

The same origin proxies three third-party services, with no API key of our own:

- [ ] `GET /weather/data/2.5/forecast/?q={city},{cc}&units=metric&lang=fr` — OpenWeatherMap 5-day/3-hour forecast, 40 entries, full OWM shape. **Works unauthenticated.** `zip={zip},{cc}` also accepted; `units` ∈ `metric`/`imperial`. Drives the dashboard weather tile.
- [ ] `GET /geocode?country={cc}&address={zip}` — GeoNames postal codes → `{postalcodes:[{postalcode, placeName, adminName1..3, lat, lng, countryCode}]}`.
- [ ] `GET /timezone?lat={lat}&lng={lng}` — GeoNames → `{timezoneId, gmtOffset, dstOffset, rawOffset, sunrise, sunset, time, countryName}`.
- [ ] `GET /siret/{siret}` — INSEE Sirene company lookup (installer onboarding).

### 2.2 Session expiry header (`auth.md`)

- [ ] `POST /api/v1/authent` returns **`x-cwt-token: <ISO-8601 instant>`** = login time **+ exactly 2 h** (measured twice, to the second). Sent **only** on the authent response, not on ordinary `GET`s — so session lifetime is knowable up front instead of being discovered via a 401.

### 2.3 Second error format (`README.md` error conventions)

- [ ] Besides RFC-7807 `problem+json`, the API also returns a **bare JSON array of Spring validation errors** with HTTP **412**:
  ```json
  [{"codes":["user.already.activated"],"arguments":[],
    "defaultMessage":null,"objectName":"","code":"user.already.activated"}]
  ```
  Observed on `users/{id}/refreshtoken`, `gateways/{id}/network`,
  `companies/installation-company-by-installer-email`. Note that anything
  assuming `problem["detail"]` breaks on these (list, not dict), and add
  `412` to the documented status codes.

### 2.4 Endpoints missing from the notes

- [ ] **Modbus group** (one undocumented JS module, worth its own section): `POST /api/devices/v2/modbus`; `GET /api/gateways/modbus-configurations` (200, `{id, name, label, port, slave, device_kinds}`); `GET /api/gateways/{gatewayUid}/scan-modbus-ip?port=502` (long-running, nginx `504` after ~60 s); `GET|POST /api/connectedobjects/{id}/modbus-expert`; `GET /api/connectedobjects/{id}/state-history`. The last two 404 on `AZUREIOT` objects — Modbus-only.
- [ ] **Account lifecycle** (base `api/users`): `POST /{email}/forgottenpasswd`; `PUT /{email}/forgottenpasswd/{token}` with `{password: <salted sha256>}`; `PUT /{email}/token/{token}`; `PUT /{id}/updateemail`; `POST /` (register); `PUT|DELETE /{id}`; `GET /{email}/isReadyForSiteInstallation` (403 for `END_USER`). Also worth an explicit warning: **`GET /api/users/{id}/refreshtoken` is not a session refresh** — it re-sends the activation mail (`412 user.already.activated` on an active account).
- [ ] **Site administration** (base `api/sites`): `GET /{id}` and `GET /by-site-uid/{siteUid}` (both 200, single site); `PUT /{siteUid}/reloadConnexionStatus`; `PUT /{id}/gateways/{gatewayUid}`; `PUT /{id}/send-installation-progress`; `POST /transfer/installForUser`; `GET /transfer/{id}/target-user-information` (404 outside a pending transfer).
- [ ] `GET /api/devices/{id}/capacities` — 200, one device's capacities without walking the `@ref` graph.
- [ ] `GET /api/plannings/configuration-modes?deviceId={id}` — the bundle now uses **kebab-case**; the old camelCase still answers 200 (Spring accepts both). Returned `["MANUAL"]` on every device tested.
- [ ] Installer/company surface: `GET /api/companies?registrationNumber={siret}`, `/api/companies/installation-company-by-installer-email?installerEmail=…`, `/api/companies/{id}/associated-sales-companies` (200 even for `END_USER`), `POST /api/companies/{id}/enable-sales-business|enable-installation-business`.
- [ ] `GET|DELETE /api/iot-platforms/{id}`, `POST /api/iot-platforms/{id}/import-resources-to-site?siteUid={uid}`, `GET /api/products/{id}`.
- [ ] `/api/tiles/{id}` answers **405** on `GET` (`PUT`/`DELETE` only).
- [ ] **Web Bluetooth**, browser-only: the SPA pairs connected objects via `navigator.bluetooth` (service UUID `00001000-1d55-54e2-83ec-2a4453c26896`), with `bluetooth_connected_object` / `scanned_access_point` entities. Unreachable from an HTTP client — document it so nobody hunts for a "pairing" endpoint.

### 2.5 Enums, pinned down by sweeping until 400 (`aggregations.md`)

- [ ] `measureKind`: `FLOW`, `QUANTITY`, `STATE`, `VALUE` (°C), `INDEX`, `RATE` (%). Rejected: `POWER`, `TEMPERATURE`.
- [ ] `aggregationLevel`: `NONE`, `HOUR`, `DAY`, `MONTH`, `YEAR`. Rejected: `WEEK`, `MINUTE`, `QUARTER`, `TEN_MINUTES`.
- [ ] `aggregationType`: `NONE`, `MIN`, `MAX`, `SUM`, `AVERAGE`. Rejected: `AVG`, `FIRST`, `LAST`, `COUNT`, `MEDIAN`.
- [ ] `timeAgoUnit`: `HOUR`, `DAY`, `WEEK`, `MONTH`, `YEAR` (here `WEEK` *is* valid). Rejected: `MINUTE`.
- [ ] `siteNetworkType` — **full set; only `PRODUCTION` was confirmed before**: `PRODUCTION`, `CONSUMPTION`, `INJECTION`, `WITHDRAWAL`, `CHARGE`, `DISCHARGE`. Rejected: `BATTERY`, `GRID`. `CHARGE`/`DISCHARGE` are the battery flows.
- [ ] Planning `mode`: `ON`, `OFF`, `COMWATT` (solar-driven). Tile `tileType`: `VALUATION`, `REAL_TIME`, `THIRD_PARTY`. Capacity `nature`: `CLAMP`, `POWER_SENSOR`, `POWER_SWITCH`, `RELAY`.

### 2.6 Planning write-path quirks

Mapped by the Kotlin client [`paulthvt/solareco`](https://github.com/paulthvt/solareco)
(active, shipped device control + planning on 2026-08-12) — **not** verified here,
so document them as second-hand until we test them:

- [ ] `PUT /api/plannings/{id}` requires `"device": {"@class": "Device", "id": <int>}`, else `400 Failed to read request`.
- [ ] Each schedule's `typicalDay` must be a **full inline object**; an id-only reference returns 500.
- [ ] The `PUT` **replaces** `typicalDaySchedules` wholesale and reassigns ids — omitted schedules are deleted.
- [ ] Schedules with `optimalPlanning: true` are server-managed: never send them back.
- [ ] `POST /api/typicaldays` takes `siteId` as a **query param**, not in the body.
- [ ] Confirmed live here: real plannings carry `activeDayMask` (bitmask, `127` = every day), `startDate`/`endDate`, `isDefault`, `status`, and auto-generated `optimalPlanning: true` rows labelled `TD-ML-{n}-Dev-{deviceId}`.

## 3. Client — read-only methods

All verified `200` live. Ordered by value/effort.

- [ ] `get_weather(city|zip, country, units='metric', lang='fr')` — the unauthenticated OWM proxy; high value for solar forecasting, no key needed.
- [ ] `get_site(site_id)` / `get_site_by_uid(site_uid)` — we only ever call the list endpoint.
- [ ] `get_device_capacities(device_id)`.
- [ ] `get_plannings(site_id)` and `get_typical_days(site_id)` — paginated (`content`, `totalPages`, `paginationSize`). **Do not** offer the `?deviceId=` variant (500).
- [ ] `get_alert_configs(device_id)` — `{period, id, min, max, activated, deviceId}`; `period` observed: `SLIDING_24_HOURS`.
- [ ] Gateway diagnostics — `get_gateway(id)`, `get_gateway_by_uid(uid)`, `get_gateway_network(gateway_uid)`, `get_gateway_ssids(gateway_id)`. Now `END_USER`-accessible; enables a "box offline / weak Wi-Fi" check. Mind the id/uid split (§1).
- [ ] `get_electricity_contract(site_id)` and `get_electricity_contract_providers()`.
- [ ] Catalogues: `get_products()`, `get_timezones()`, `get_modbus_configurations()`.
- [ ] `get_connected_object_devices(connected_object_id)`.

## 4. Client — behaviour

- [ ] Capture `x-cwt-token` at login and expose it (e.g. `client.session_expires_at`); optionally re-authenticate proactively instead of waiting for a 401.
- [ ] Handle the **412 + array-of-codes** error shape in `_response_detail` / `_api_error`, and surface the `code` (e.g. `user.already.activated`) instead of crashing on a list.
- [ ] `stream_measurements`: send the literal text `__ping__` every **60 s** and `SEND /app/streaming/stop` on teardown, mirroring the SPA.
- [ ] Align the docstring enums with §2.5 — drop `WEEK` from `aggregation_level`, document the `siteNetworkType` set including `CHARGE`/`DISCHARGE` for batteries.

## 5. Client — write paths

Need a consenting test site; quirks in §2.6.

- [ ] `set_device_mode(device_id, ON|OFF|COMWATT)` — the "Off / On / Auto" control.
- [ ] Create/update typical days, update a planning.
- [ ] `set_alert_config(device_id, min, max, period, activated)`.
- [ ] Confirm the `state` values for `set_pilot_wire` / `set_thermal_mode`, still unverified: no pilot-wire device was reachable, and every `selectValues` seen live was `null`.

## Out of scope

- Web Bluetooth pairing (browser-only API, cannot be driven over HTTP).
- Installer / back-office endpoints (`backoffice/*`, `users?omniSearch=`, site profile): 403 for `END_USER`, so untestable and out of this client's audience.
