# Devices, capacities, gateways

## `GET /api/devices?siteId={siteId}`

Returns the array of devices for a site. The response is **JSON-with-refs**:
the first time an object appears it carries a `"@id": "N"`; later occurrences
of the same object are `{"@ref": "N"}`. Any client that walks the tree must
handle that.

A device looks like:

```jsonc
{
  "@class": "Device",
  "@id": "1",
  "id": 23593,
  "name": "solaire en autoproduction",
  "sourceIsOnline": true,
  "site": { ... },                  // back-ref to the site
  "deviceKind": { "code": "SOLAR_PANEL", "category": "...", ... },
  "configuration": { "power": null, ... },
  "features": [
    {
      "id": 442832,
      "feature": { "code": "PROFILING", "featureName": "PROFILING" },
      "enabled": true,
      "capacities": [ ... ]         // <-- the actual sensors / actuators
    },
    ...
  ],
  "capacities": [...],              // duplicate convenience array
  "archived": false,
  "coState": "...",
  "partNature": "...",
  "threePhase": false,
  "partChilds": [...], "partChild": ..., "partKind": ...,
  "global": false, "production": false
}
```

### Capacities

A *capacity* is the atomic measurable / actionable thing on a device — a
clamp, a relay, a pilot wire, a thermostat, etc. Sample capacity:

```jsonc
{
  "id": 48067,
  "capacityId": "AZUREIOT-co.1.instances.1.sensor.1.data",
  "type": "SENSOR",          // or "ACTUATOR"
  "nature": "CLAMP",         // CLAMP, RELAY, PILOT_WIRE, THERMOSTAT, ...
  "sgReady": false,
  "instance": "co.1.instances.1",
  "connectedObjectId": 8107,
  "measureKinds": ["FLOW"],  // possibilities the capacity can produce
  "measureKind": "FLOW",     // current selection
  "measureType": { "code": "ELECTRICITY", "measureKinds": ["STATE","FLOW","QUANTITY"] },
  "deviceId": 23593,
  "global": true,
  "production": true,
  "enable": false,
  "phase": "POSITIVE_2",
  "calibration": 60,
  "valorisationIndex": 1,
  ...
}
```

A capacity has **two** ids — easy to confuse:

- `id` (numeric, e.g. `48067`) — the primary key. **All
  `/api/capacities/{id}/...` URLs take this one** (see
  [`capacities.md`](capacities.md)).
- `capacityId` (opaque string, e.g.
  `"AZUREIOT-co.1.instances.1.sensor.1.data"`) — gateway-side identifier.
  This is the value echoed in WebSocket streaming frames (see
  [`websocket-realtime.md`](websocket-realtime.md)) and the right key for
  mapping `WS frame → entity`.

For one device's capacities without walking the `@ref` graph, use
`GET /api/devices/{id}/capacities` ([Single device](#single-device)):
the site-wide listing deduplicates repeated entities (devices,
capacities) into fastjson `@ref` pointers, while the dedicated endpoint
always returns full objects.

## Single device

- `GET  /api/devices/{deviceId}` — full device document.
- `GET  /api/devices/{deviceId}/capacities` — **200**, this device's
  capacities as an array of full objects — no `@ref` indirection to
  resolve (live-verified 2026-10-11).
- `PUT  /api/devices/{deviceId}` — update device (name, configuration, etc.).
  Already wrapped by `ComwattClient.put_device`.
- `PUT  /api/devices/{deviceId}?autoset=true` — same with the autoset flag.
- `GET  /api/devices/{deviceId}/hasAutoSet`
- `PUT  /api/devices/{deviceId}/mode`
- `PUT  /api/devices/{deviceId}/reverse_grid_meter`
- `POST /api/devices/{deviceId}/connected_object`
- `DELETE /api/devices/{deviceId}/remove`
- `POST /api/devices/v2/modbus` — pair a Modbus device (installer flow;
  see [Modbus group](#modbus-group)).

## Device kinds (catalogue)

- `GET /api/devicekinds/by-site-uid/{siteUid}` — returns the catalogue of
  device kinds available for the site (47 entries on the test account). Each
  entry:

  ```
  id, code (e.g. PRO_HEAT_PUMP, SOLAR_PANEL, GRID_METER, FREEZER, ...),
  category, icon, displayOrder,
  global, onlyInfo, production, injection, withdrawal,
  features, codeEnum, eligibleToSgReady, partKindId
  ```

This is what powers the "add a device" picker in the UI.

## Connected objects

A *connected object* is the physical thing that exposes capacities to the
gateway (the inverter, the smart meter, the pluggable relay box, etc.).
Broader than `/api/devices` — it also surfaces gateway-level entries.

- `GET  /api/connectedobjects?siteId={siteId}` — every connected object
  on the site with its capacities. Use this to enumerate every capacity
  on the site in one call.
- `GET  /api/connectedobjects?gatewayUid={uid}` — filter by gateway.
- `GET  /api/connectedobjects/{connectedObjectId}`
- `GET  /api/connectedobjects/{connectedObjectId}/devices`
- `GET  /api/connectedobjects/{connectedObjectId}/modbus-expert`
  (see [Modbus group](#modbus-group))
- `POST /api/connectedobjects/` — pair a new connected object.

> ⚠ **The physical pairing is browser-only (Web Bluetooth).** The SPA
> performs the BLE handshake via `navigator.bluetooth` (service UUID
> `00001000-1d55-54e2-83ec-2a4453c26896`), over the bundle entities
> `bluetooth_connected_object` / `scanned_access_point` (2026-09 bundle
> re-exploration — not live-verifiable from an HTTP client). There is **no
> HTTP pairing endpoint** to hunt for: the `POST` above only creates the
> server-side record; a plain HTTP client cannot reach the BLE step.

## Gateways

The Comwatt box itself (the `OCTOPUS_*` IoT gateway).

Gateway **reads** are open to a normal `END_USER` (re-verified 2026-09-06
across the probe account's six gateways — 3 × `POWER_GEN_4`, 2 ×
`MONITOR_GEN_4` SmartPlugs, 1 × `ACCESSORY`): the three `GET`s below
return `200` with the full gateway document (JSON-with-refs — handle
`@ref` like everywhere else):

```
id, gatewayUid, connected, connectionEvent, updating, status,
associateDate, createDate, updateDate, lotId, name,
networkConfiguration, product, installer, salesCompany,
connectedObjectReference
```

`connected` / `updating` / `status` are the "box offline / being
updated" flags a health check wants.

- `GET  /api/gateways/{gatewayId}` — `200` for `END_USER`.
- `GET  /api/gateways/{gatewayId}/network`
- `POST /api/gateways/{gatewayId}/netconnect`
- `GET  /api/gateways/{gatewayId}/ssids`
- `GET  /api/gateways/{gatewayId}/with-sales-company` — `200` for
  `END_USER`; same key set as the plain `{gatewayId}` read.
- `GET  /api/gateways/by-gateway-uid/{GATEWAY_UID}` — `200` for
  `END_USER`.
- `GET  /api/gateways/{gatewayUid}/scan-modbus-ip?port={port}`
  (see [Modbus group](#modbus-group))

> ⚠ **Two-ids trap (live-verified 2026-09-06).** The `{gatewayId}` path
> segment above is **misleading**: the three sub-resource endpoints do
> **not** all take the same id. A gateway has two ids — the numeric
> primary key (`id`, e.g. `359`) and the opaque `gatewayUid` string
> (e.g. `"BXCCBB77D9"`, also surfaced as `siteUid`-adjacent) — and the
> endpoints split on them:
>
> | endpoint | takes | wrong id → |
> | --- | --- | --- |
> | `/api/gateways/{id}` (plain read) | numeric `id` | gatewayUid → Spring `400 Failed to convert 'gatewayId'` |
> | `/api/gateways/{id}/network` | `gatewayUid` | numeric `id` → `412 gateway.not.found.for.fetching.network.details` (bare JSON array of Spring errors, **not** problem+json — see [error conventions](README.md#error--status-code-conventions)) |
> | `/api/gateways/{id}/ssids` | numeric `id` | gatewayUid → `400 "Failed to convert 'gatewayId' with value: '...'"` (problem+json) |
> | `/api/gateways/{id}/scan-modbus-ip` | `gatewayUid` | numeric `id` → `403` (empty body); the `gatewayUid` form actually triggers the Modbus scan (long-running) |
>
> So `/network` and `/scan-modbus-ip` want the **`gatewayUid`**, while
> `/ssids` (and the plain `{gatewayId}` read) want the **numeric `id`**.
> This is the third instance of the same trap as capacities (`id` vs
> `capacityId`) and sites (`id` vs `siteUid`). The `{gatewayId}` placeholder
> in the URL signatures above is kept for brevity; resolve it per endpoint
> using the table.

> ⚠ **Correction (2026-09-06).** `by-gateway-uid` was previously
> documented as `403` for `END_USER` (admin-only). Not reproducible:
> all three gateway reads return `200` on every gateway of the account
> with a plain `END_USER` session. Either the role check was lifted
> server-side since the last pass, or those earlier probes hit another
> role boundary.

## Modbus group

One JS module in the SPA bundle, spanning devices, gateways and connected
objects. Modbus is installer-world: on a plain `END_USER` account most of
the group is only observable through its error behaviour (2026-08-15
recon; live re-probe 2026-10-11 on an account whose objects are all
`AZUREIOT`).

- `POST /api/devices/v2/modbus` — pair a Modbus device (installer flow;
  bundle only, not live-probed). The bundle also references a
  `* /api/devices/v2/modbus` sub-API.
- `GET /api/gateways/modbus-configurations` — **200**, the Modbus catalogue
  (live-verified 2026-10-11: 4 entries). Entry shape:

  ```json
  {
    "id": 1,
    "name": "huawei",
    "label": "Huaweï Sun2000 nKTL",
    "port": 502,
    "slave": 1,
    "device_kinds": ["SOLAR_PANEL", "BATTERY", "GRID_METER"]
  }
  ```

- `GET /api/gateways/{gatewayUid}/scan-modbus-ip?port={port}` — triggers an
  actual Modbus scan on the gateway. Long-running: nginx cuts it with a
  **504 after ~60 s**. Takes the `gatewayUid` (see the two-ids trap
  above).
- `GET|POST /api/connectedobjects/{id}/modbus-expert` — Modbus expert
  parameters of a connected object.
- `GET /api/connectedobjects/{id}/state-history` — Modbus state history.

The last two are **Modbus-only**: on a connected object without a Modbus
configuration (every `AZUREIOT` object) both return **`404`** — in the
bare-array error format, not problem+json (live-verified 2026-10-11; see
[error conventions](README.md#error--status-code-conventions)):

```json
[
  {
    "codes": [
      "No Modbus configuration associated with ConnectedObject id: {id}"
    ],
    "arguments": [],
    "defaultMessage": null,
    "objectName": "",
    "field": "",
    "code": "No Modbus configuration associated with ConnectedObject id: {id}"
  }
]
```

The message echoes the path id, and the entry carries a `field` key on top
of the shape documented in the error conventions. `POST modbus-expert` is
a write path and was not live-probed.
