# Misc endpoints

## Non-/api proxies

The same origin also proxies third-party services under non-`/api` paths,
with no Comwatt API key of our own — OpenWeatherMap, GeoNames and INSEE
Sirene below.

### Weather (OpenWeatherMap)

- `GET /weather/data/2.5/forecast/` — OpenWeatherMap 5-day / 3-hour
  forecast. **Works unauthenticated** (verified live 2026-10-11); drives
  the dashboard weather tile. OWM query semantics:
  - `q={city},{cc}` or `zip={zip},{cc}` — location; e.g. `q=Paris,fr`,
    `zip=33000,fr` → Bordeaux. Unknown city → `404` with the OWM JSON
    error `{"cod":"404","message":"city not found"}` (verified live).
  - `units=metric|imperial` and `lang=fr` (localized
    `weather[].description`, e.g. `"couvert"`).
  - Trailing slash optional: `/forecast/` and `/forecast` both answer
    `200` — the initial field note requiring the slash was wrong.

  Full OWM shape, `cnt` = 40 entries (captured live 2026-10-11):

  ```jsonc
  {
    "cod": "200", "message": 0, "cnt": 40,
    "list": [
      {
        "dt": 1791720000, "dt_txt": "2026-10-11 12:00:00",
        "main": { "temp": 14.96, "feels_like": 14.34,
                  "temp_min": 14.96, "temp_max": 15.99,
                  "pressure": 1016, "sea_level": 1016,
                  "grnd_level": 1007, "humidity": 70,
                  "temp_kf": -1.03, "dew_point": 9.54 },
        "weather": [ { "id": 804, "main": "Clouds",
                       "description": "couvert", "icon": "04d" } ],
        "clouds": { "all": 100 },
        "wind": { "speed": 3.63, "deg": 273, "gust": 8.79 },
        "visibility": 10000,
        "pop": 0,
        "sys": { "pod": "d" }
      }
      // … 39 more entries, one per 3 h slot
    ],
    "city": {
      "id": 2988507, "name": "Paris",
      "coord": { "lat": 48.8534, "lon": 2.3488 },
      "country": "FR", "population": 2138551, "timezone": 7200,
      "sunrise": 1791698661, "sunset": 1791738607
    }
  }
  ```

  ⚠ **Caveat — burst rate limiter.** A burst of consecutive calls trips
  an infrastructure-level `429 Too Many Requests` whose body is **HTML**
  (not OWM's JSON error shape — `via: 1.1 google` on the response), so
  don't parse errors as JSON unconditionally. Observed live 2026-10-11;
  clears within seconds.

### Geocode (GeoNames)

- `GET /geocode?country={cc}&address={zip or place}` — GeoNames postal
  code / place-name lookup. **Works unauthenticated** (verified live
  2026-10-11). `address` matches postal codes and place names alike;
  results cap at 20 rows (GeoNames default) and there is no prefix
  matching — a partial code returns nothing:
  - `country=fr&address=33000` → 1 row (Bordeaux);
    `country=fr&address=75001` → 2 rows (`Paris`, `Paris 01`);
    `country=fr&address=33` → `[]`.
  - Place-name queries go through GeoNames full-text search, whose
    matches can be oblique (`address=Bordeaux` → the Paris 01–04
    arrondissements among its 20 rows).
  - Missing params or unknown country → `200 {"postalcodes":[]}` — the
    proxy never errors on bad input.

  Row shape (captured live 2026-10-11) — richer than the roadmap note:
  the `adminCode1..3` fields are present too:

  ```jsonc
  {
    "postalcodes": [
      { "postalcode": "33000", "placeName": "Bordeaux",
        "countryCode": "FR", "lat": 44.840439, "lng": -0.5805,
        "adminName1": "Nouvelle-Aquitaine", "adminCode1": "75",
        "adminName2": "Gironde",         "adminCode2": "33",
        "adminName3": "Bordeaux",        "adminCode3": "332" }
    ]
  }
  ```

### Timezone (GeoNames)

- `GET /timezone?lat={lat}&lng={lng}` — GeoNames timezone lookup.
  **Works unauthenticated** (verified live 2026-10-11). Dates are local
  to the requested location, `YYYY-MM-DD HH:mm`:

  ```jsonc
  {
    "timezoneId": "Europe/Paris",
    "gmtOffset": 1, "dstOffset": 2, "rawOffset": 1,
    "time": "2026-10-11 12:45",
    "sunrise": "2026-10-11 08:12", "sunset": "2026-10-11 19:24",
    "countryCode": "FR", "countryName": "France",
    "lat": 44.8404, "lng": -0.5805   // echoed back
  }
  ```

  Richer than the roadmap note: `countryCode` and the echoed `lat`/`lng`
  are present too.

  ⚠ **Caveat — errors come back as `200`.** Unlike the weather proxy,
  which passes OpenWeatherMap's HTTP `404` through, this proxy wraps
  GeoNames errors in `200 OK` with a `status` object (GeoNames code
  `14`): missing params → `{"status":{"message":"missing parameter ","value":14}}`,
  out-of-range coords → `{"status":{"message":"invalid lat/lng","value":14}}`
  (both verified live). Check for `timezoneId` — or a `status` key — before
  consuming the response.

### Siret (INSEE Sirene)

- `GET /siret/{siret}` — INSEE Sirene company lookup (installer
  onboarding). **Works unauthenticated** (verified live 2026-10-11 via
  the error paths). Unlike the GeoNames proxies, errors pass through as
  real HTTP statuses with the native INSEE error shape (French messages,
  `header.statut`):
  - unknown but well-formed SIRET → `404`:
    `{"header":{"statut":404,"message":"Aucun élément trouvé pour le siret 12345678901234"}}`
  - malformed SIRET (not 14 digits) → `400`:
    `{"header":{"statut":400,"message":"Erreur de format de siret (abc) - Format attendu : 14 chiffres"}}`

  ⚠ **Caveat — success shape unverified.** Lookups of **existing**
  companies (La Poste `35600000000048`, Air France `55210055400013`)
  consistently answered `429` with an **HTML** body (infra-style burst
  limiter, `via: 1.1 google`) from the very first attempt on 2026-10-11,
  while unknown/malformed SIRETs answered normally — so the success
  body could not be captured. Capturing it is tracked in
  [issue #120](https://git.greil.fr/mat/python-comwatt-client/issues/120).

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

- `GET /api/plannings/configuration-modes?deviceId={deviceId}` — the legal
  configuration modes for a device: `["MANUAL"]` on every device tested
  (4 devices, live-verified 2026-10-11). The bundle now spells it
  **kebab-case**; the older camelCase `configurationModes` still answers
  `200` — Spring accepts both.
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
