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

## Single device

- `GET  /api/devices/{deviceId}` — full device document.
- `PUT  /api/devices/{deviceId}` — update device (name, configuration, etc.).
  Already wrapped by `ComwattClient.put_device`.
- `PUT  /api/devices/{deviceId}?autoset=true` — same with the autoset flag.
- `GET  /api/devices/{deviceId}/hasAutoSet`
- `PUT  /api/devices/{deviceId}/mode`
- `PUT  /api/devices/{deviceId}/reverse_grid_meter`
- `POST /api/devices/{deviceId}/connected_object`
- `DELETE /api/devices/{deviceId}/remove`
- `POST /api/devices/v2/modbus` — pair a Modbus device (installer flow).
- `*    /api/devices/v2/modbus` — Modbus device sub-API.

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
- `POST /api/connectedobjects/` — pair a new connected object.

## Gateways

The Comwatt box itself (the `OCTOPUS_*` IoT gateway).

- `GET  /api/gateways/{gatewayId}`
- `GET  /api/gateways/{gatewayId}/diagnostic`
- `GET  /api/gateways/{gatewayId}/network`
- `POST /api/gateways/{gatewayId}/netconnect`
- `GET  /api/gateways/{gatewayId}/ssids`
- `GET  /api/gateways/{gatewayId}/with-sales-company`
- `GET  /api/gateways/by-gateway-uid/{GATEWAY_UID}` — 403 for `END_USER`
  (admin-only).
- `GET  /api/gateways/{gatewayUid}/scan-modbus-ip?port={port}`
