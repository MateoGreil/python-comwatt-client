# Misc endpoints

## Tempo / tariff / grid forecast

- `GET /api/electricityprice?siteId={siteId}` — EDF Tempo calendar + current
  tariff structure. Live response shape:

  ```jsonc
  {
    "tempoSyntheses": {
      "WHITE": { "numberOfDays": 38, "totalNumberOfDays": 43 },
      "BLUE":  { "numberOfDays": 177, "totalNumberOfDays": 300 },
      "RED":   { "numberOfDays": 22,  "totalNumberOfDays": 22  }
    },
    "daily": [
      { "date": "2026-04-24", "dayValue": "BLUE",
        "status": [
          { "value": "BLUE", "type": "OFFPEAK", "start_time": "00:00", "end_time": "06:00" },
          { "value": "BLUE", "type": "PEAK",    "start_time": "06:00", "end_time": "22:00" },
          { "value": "BLUE", "type": "OFFPEAK", "start_time": "22:00", "end_time": "23:59" }
        ] },
      ...
    ],
    "tempoSynthesesComplete": true
  }
  ```

- `GET /api/ecowatt` — RTE EcoWatt forecast. Array of:

  ```
  { id, updatedAt, retrievedAt, date, status (GREEN/ORANGE/RED),
    hourly: [VIRTUOUS_GREEN, VIRTUOUS_GREEN, ...] }   # 24 entries
  ```

- `GET /api/electricitycontract/providers` — flat list of provider names
  the app knows about (`EDF`, `TotalEnergies`, `Octopus`, `Mint`,
  `Ekwateur`, …).
- `GET|PUT /api/electricitycontract/{id}` — the contract of a given site.
  ⚠ **TODO:** the required query parameter has not been pinned down.
  `?siteId=` returns 404; trailing-slash variants return 404; the bundle
  builds the URL dynamically so the param name is opaque. Inspect the
  Network tab in the SPA to confirm before relying on this endpoint.

## Catalogues

- `GET /api/devicekinds/by-site-uid/{siteUid}` — device-kind catalogue for
  the site (47 items on test). See [`devices.md`](devices.md).
- `GET /api/util/timezones` — static list of `{timeZone, posix}` pairs.
- `GET /api/iot-platforms` — list of IoT platforms (used internally).
- `GET /api/products` — Comwatt hardware catalogue
  (`MONITOR_GEN_4`, `POWER_GEN_4`, …).
- `GET /api/products/{id}` — single product.
- `GET /api/companies` — requires an `id` or similar (returned 400 with no
  query).

## Connected objects

See [`devices.md#connected-objects`](devices.md#connected-objects) for the
full list (`/api/connectedobjects?siteId=`, `?gatewayUid=`, by-id, etc.).

## Plannings / schedules

- `GET /api/plannings?deviceId={deviceId}` — paginated plannings for a
  device. Empty for most devices.
- `GET /api/plannings/configurationModes?deviceId={deviceId}` — the legal
  configuration modes for a device (e.g. `["MANUAL"]`).
- `GET /api/plannings/?siteId={siteId}` — site-wide variant; returns 404
  when the user has no plannings (Spring's default behaviour for empty
  result sets, not a missing endpoint).
- `POST /api/plannings` — create.
- `GET|PUT|DELETE /api/plannings/{planningId}`

## Typical days

- `GET /api/typicaldays?siteId={siteId}` — paginated list of "typical day"
  templates: time-range + mode (ON/OFF/AUTO/…) rows that drive the
  auto-consumption optimizer.
- `POST /api/typicaldays?siteId={siteId}` — create.
- `GET|PUT|DELETE /api/typicaldays/{id}`

## Alerts

- `GET /api/alertconfigs/v2?deviceId={deviceId}` — current threshold
  config for a device:
  `{period, id, min, max, activated, deviceId}` (live 2026-07-04; `max` may
  be `null`). Observed `period` values include `SLIDING_24_HOURS`.
- `GET     /api/alertconfigs/v2` — list / create.
- `GET|PUT /api/alertconfigs/v2/{id}`

## Thermal control

- `GET /api/thermalcontrol?deviceId={deviceId}` — 200 with empty body on
  non-thermal devices; presumably returns set-point / mode on
  thermostats and water heaters.
- `PUT /api/thermalcontrol/{id}` — update set-point / mode.
- `*   /api/thermalcontrol/{id}` — thermal-control configuration per
  device.

## Users (admin / installer)

- `GET /api/users?omniSearch={str}` — fuzzy user search; installer-only
  (403 for `END_USER`).

## Delegated access

- `GET /api/delegatedaccess?owner={bool}&page={n}` — paginated list of
  delegations.
- `GET /api/delegatedaccess?owner=false&omniSearch={str}` — fuzzy search.
- `POST /api/delegatedaccess` — grant access.
- `DELETE /api/delegatedaccess/{id}` — revoke.

## Back office / installer-only (403 for normal users)

- `GET  /api/backoffice/information/{...}`
- `GET  /api/backoffice/stock/status?...`
- `PUT  /api/backoffice/stock/activate?...`
- `PUT  /api/backoffice/stock/product?...`
- `POST /api/backoffice/stock/deactivate`
- `GET  /api/sites/{siteId}/profile`
