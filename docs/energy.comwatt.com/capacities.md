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
| `PUT /api/capacities/{id}/pilot-wire?state={STATE}` | Set a pilot-wire heater state. |
| `PUT /api/capacities/{id}/thermal-mode?state={STATE}` | Set thermal mode (e.g. eco / comfort). |
| `PUT /api/capacities/{id}/thermostat-set-point?value={value}` | Set a thermostat target. |
| `PUT /api/capacities/` | Batch update capacities (referenced in bundle). |
| `POST /api/capacities/process-phase-diagnostic-on-capacities` | Phase diagnostic helper (referenced in bundle). |
| `POST /api/capacities/process-phase-auto-diagnostic-on-capacities?isDeviceBiDirectional={bool}` | Automated phase diagnostic. |

### `state` enum values — TODO: confirm

> ⚠ **Unconfirmed.** The exact `state` values for `pilot-wire` and
> `thermal-mode` are **not** visible as string literals in the bundle —
> they are passed straight through from a React state to the URL query
> param. Plausible candidates from generic Comwatt usage are
> `COMFORT`, `ECO`, `FROST`, `OFF` (pilot wire) and `COMFORT`, `ECO`,
> `OFF` (thermal mode), but a client author **must** confirm against the
> live capacity object's `selectValues` field (or by sniffing the SPA
> Network tab) before relying on them. Sending an unsupported value is
> likely to 400.

## Realtime feedback

Once you successfully call any of these endpoints, a STOMP message is
pushed on `/topic/sites/{siteUid}/capacityChanged` carrying the updated
capacity. The same channel — once activated with
`SEND /app/streaming/start` — also streams live `FLOW` / `STATE` /
`VALUE` measurements for every capacity on the site. See
[`websocket-realtime.md`](websocket-realtime.md) for the full handshake
and frame shapes.
