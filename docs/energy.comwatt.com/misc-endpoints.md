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
- `GET /api/electricitycontract/{id}` — the electricity contract(s) of a
  given site. **Verified live 2026-09-06:** the path parameter is the
  **numeric site id** (not the `siteUid`), **no query parameter** is
  involved, and the response is a **JSON array** — `[]` when the site has
  no contract. The earlier "required query parameter" TODO was a false
  lead: the collection path `/api/electricitycontract?siteId=` simply has
  no handler (404); the per-site contract lives at the `{id}` path segment.

  ⚠ **Caveats.** The server does not 404 on an unknown id — on the probe
  account both the `siteUid` and a bogus numeric id also return `200 []` —
  so "site id" semantics rest on the SPA bundle (which builds the URL from
  the numeric site id), not on server-side validation. The non-empty array
  shape is **unverified**: the probe site carries no contract, so the item
  keys shown below come from the SPA bundle, not a live response.

  ```jsonc
  // [] when the site has no contract; otherwise an array of contract
  // objects (shape unverified live — no contract on the probe site):
  [
    { "id": 7, "provider": "EDF", "siteId": 3349 /* , … */ }
  ]
  ```
- `PUT /api/electricitycontract/{id}` — update a site's contract. **Not
  verified live** (write path; no consenting test contract to mutate).

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
  device. `200` on every device tested (re-verified 2026-09-06: 19
  devices, 13 kinds); `content` empty for most — on the probe account
  only the schedulable loads (washing machine, dishwasher) carried one.

  > ⚠ **Correction (2026-09-06).** An earlier version of this note (and
  > the roadmap) claimed this variant answered `500 Internal error`,
  > making the per-device planning view unusable. Not reproducible:
  > every device kind returns `200`. Either fixed server-side since
  > 2026-08-15, or a bad probe URL back then.

- `GET /api/plannings?siteId={siteId}` — `200` paginated; **no trailing
  slash**. `siteId` is accepted but appears ignored: a bogus id — or no
  id at all — returns the same list of the authenticated user's
  plannings (re-verified 2026-09-06). Treat it as "all my plannings".

  > ⚠ **Correction (2026-09-06).** This was previously documented as
  > `GET /api/plannings/?siteId=` "returns 404 when the user has no
  > plannings — Spring's default behaviour for empty result sets".
  > Misdiagnosis: the trailing-slash URL answers `404` with
  > `No static resource api/plannings.` (Spring's static-handler
  > fallthrough for an unmatched path) even for a site that **has**
  > plannings, while the same query without the slash returns `200`
  > with its plannings. There is no "404 on empty list" behaviour.

- `GET /api/plannings/configurationModes?deviceId={deviceId}` — the legal
  configuration modes for a device (e.g. `["MANUAL"]`).
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
