# Capacities — switching things on and off

A *capacity* of type `ACTUATOR` (and certain sensors) can be controlled via
the `/api/capacities/{id}/...` family.

> ⚠ **Terminology trap.** A capacity object has **two** ids:
> - `id` — the numeric primary key (e.g. `48067`). **This is what the
>   URL path takes.**
> - `capacityId` — an opaque string (e.g.
>   `"AZUREIOT-co.1.instances.1.sensor.1.data"`) used by the gateway and
>   echoed in WebSocket streaming frames.
>
> All `/api/capacities/{...}` URLs below take the **numeric `id`**, not
> the `capacityId` string. See [`devices.md`](devices.md) for the full
> capacity payload.

| Endpoint | Use |
|---|---|
| `PUT /api/capacities/{id}/switch?enable={true|false}` | Toggle a relay (already wrapped by `ComwattClient.switch_capacity`). |
| `PUT /api/capacities/{id}/pilot-wire?state={STATE}` | Set a pilot-wire heater state. Requires a select capacity (else `412 capacity.is.not.a.select`); `state` is not enum-bound (any string passes binding) and valid orders remain unverified — check `selectValues` (live-verified 2026-10-27). |
| `PUT /api/capacities/{id}/thermal-mode?state={STATE}` | Set thermal mode: `state` is enum-bound to `OFF` / `HEAT` / `COOL` (live-pinned 2026-10-27; 42 candidates swept, any other value → `400 "Failed to convert 'state' …"`). Requires a select capacity (else `412 capacity.is.not.a.select`); check `selectValues`. |
| `PUT /api/capacities/{id}/thermostat-set-point?value={value}` | Set a thermostat target. |
| `PUT /api/capacities/` | Batch update capacities (referenced in bundle). |
| `POST /api/capacities/process-phase-diagnostic-on-capacities` | Phase diagnostic helper (referenced in bundle). |
| `POST /api/capacities/process-phase-auto-diagnostic-on-capacities?isDeviceBiDirectional={bool}` | Automated phase diagnostic. |

### `state` values — live-verified 2026-10-27

The bundle never spells the `state` values out (the SPA passes a React
state straight into the query param), so they were pinned by a live
enum-binding sweep: sending candidate values to both endpoints against
a non-select sensor capacity and reading the error back.

- **`thermal-mode` is server-side enum-bound.** Of 42 swept candidates,
  only `OFF`, `HEAT`, `COOL` pass the binding; every other value —
  including the previously guessed `ECO` and `COMFORT` — is rejected
  with `400 "Failed to convert 'state' with value: '…'"`.
- **`pilot-wire` is not enum-bound.** Any string passes the binding, so
  the endpoint returns no 400 signal on which orders the backend
  accepts; valid pilot-wire orders remain unverified (no pilot-wire
  hardware on the probe account).
- **Both endpoints require a "select" capacity.** A `state` value that
  passes the binding then hits the business check and is rejected with
  `412 capacity.is.not.a.select` on a non-select capacity.
- Check the live capacity's `selectValues` field for the values valid
  on your hardware (or sniff the SPA Network tab).

## Realtime feedback

Once you successfully call any of these endpoints, a STOMP message is
pushed on `/topic/sites/{siteUid}/capacityChanged` carrying the updated
capacity. The same channel — once activated with
`SEND /app/streaming/start` — also streams live `FLOW` / `STATE` /
`VALUE` measurements for every capacity on the site. See
[`websocket-realtime.md`](websocket-realtime.md) for the full handshake
and frame shapes.
