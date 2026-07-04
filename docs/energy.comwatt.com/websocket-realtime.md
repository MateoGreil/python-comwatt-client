# WebSocket / realtime (STOMP)

The Comwatt SPA pushes live data to the browser over a
**STOMP-over-WebSocket** connection. Two distinct kinds of frames are
emitted on the same connection:

1. **`capacityChanged`** — a relay/pilot-wire/thermostat **state** has
   just changed (someone flipped a switch).
2. **Streaming measurements** — live `FLOW` (W), `STATE` (on/off),
   `QUANTITY` (Wh), `VALUE` (°C), … pushed continuously **once the
   client opts in** with `SEND /app/streaming/start`.

The streaming channel is what lets the SPA show second-by-second power
without polling. It is also the mechanism that makes a streaming-first
HA integration possible.

## Endpoint

```
wss://frontage.energy.comwatt.com/ws
```

Built at runtime by the SPA from `window.location.hostname`:

```js
return "".concat(e.startsWith("https") ? "wss" : "ws", "://frontage.")
       .concat(window.location.hostname, "/ws");
```

## Authentication

The same `cwt_session` cookie used for HTTP. A browser sends it
automatically; a non-browser client must pass `Cookie: cwt_session=...`
on the `Upgrade` request. No additional token, header, or query
parameter is required.

A naive `curl` probe with `Upgrade: websocket` returns
`400 Can "Upgrade" only to "WebSocket".` — Spring's WS handler is
case-sensitive, but the response confirms the endpoint is alive.

## Protocol

Plain **STOMP 1.1 / 1.2** over raw WebSocket frames (advertised:
`v10.stomp` / `v11.stomp` / `v12.stomp`). The browser uses
[`stompjs`](https://github.com/stomp-js/stompjs). No SockJS fallback URL
(`/ws/info`, `/ws/iframe.html`, …) was found in the bundle — it is raw
WebSocket transport only.

Every STOMP frame is terminated by a `NUL` byte (`\x00`):

```
COMMAND
header1:value1
header2:value2

<optional body>
<NUL>
```

### Handshake

```
CONNECT
accept-version:1.1,1.2
heart-beat:10000,10000

<NUL>
```

Server replies:

```
CONNECTED
version:1.2
heart-beat:0,0
user-name:<authenticated email>
```

`heart-beat:0,0` — the server declines STOMP-level heart-beating. The
SPA instead sends raw text `__ping__` on the WebSocket (outside STOMP)
as a no-op keep-alive; the server ignores it.

### Enabling the measurement stream

> **Verification status:** ✅ **confirmed working live on 2026-07-04.**
> After `CONNECT` + subscribe + `SEND /app/streaming/start {"siteId": <id>}`,
> the broker pushed live `FLOW` (W) and `STATE` (on/off) frames within
> seconds. **Crucial correction:** those measurement frames are delivered on
> the **`siteUid`** topic (`/topic/sites/{siteUid}/capacityChanged`), **not**
> the numeric-id topic. Subscribing only to `/topic/sites/{numericId}/...`
> receives **nothing** after `start` — that mistake made an earlier pass
> believe streaming did not work. The SPA subscribes to *both* topics, which
> is why it works there.

**Subscriptions alone do NOT trigger the server to push measurements.**
The client must explicitly request the stream:

```
SEND
destination:/app/streaming/start
content-type:application/json

{"siteId": 3349}<NUL>
```

The payload requires the **numeric `siteId`** (the `id` field of the
site, not the short `siteUid` string). To stop:

```
SEND
destination:/app/streaming/stop

<NUL>
```

After `start`, `MESSAGE` frames begin arriving on any matching
subscription. The `SEND /app/streaming/start` must be reissued after
any reconnect / `DISCONNECT`.

### Full session — copy-pasteable

A complete client → server frame sequence to bring a single site online,
using site numeric id `3349` / `siteUid` `992179e1` and STOMP 1.2. The
streaming measurements are pushed on the **`siteUid`** topic, so you must
subscribe to it (subscribing only to the numeric-id topic yields nothing):

```
> CONNECT
> accept-version:1.1,1.2
> heart-beat:10000,10000
>
> <NUL>

< CONNECTED
< version:1.2
< heart-beat:0,0
< user-name:user@example.com
<

> SUBSCRIBE                       # numeric-id topic (state changes only)
> id:sub-0
> destination:/topic/sites/3349/capacityChanged
> ack:auto
>
> <NUL>

> SUBSCRIBE                       # siteUid topic — REQUIRED for streaming
> id:sub-1
> destination:/topic/sites/992179e1/capacityChanged
> ack:auto
>
> <NUL>

> SEND
> destination:/app/streaming/start
> content-type:application/json
> content-length:16
>
> {"siteId": 3349}<NUL>

< MESSAGE                         # note: arrives on the siteUid subscription
< destination:/topic/sites/992179e1/capacityChanged
< content-type:application/json
< subscription:sub-1
< message-id:abc-1
< content-length:...
<
< {"gatewayUid":"BX2A4B84F9","measures":[{"capacityId":"AZUREIOT-co.2.instances.0.sensor.0.withdrawal.data","measureKind":"FLOW","value":"307.0"}]}<NUL>
```

Notes:
- `id:` on `SUBSCRIBE` is required by STOMP 1.2 — use any unique
  client-side string per subscription (the SPA uses `sub-0`, `sub-1`, …).
- `ack:auto` is the SPA's choice (no client ACK needed).
- `content-length:` is optional but recommended on `SEND` with a body —
  the broker tolerates its absence.
- To gracefully shut down, send `DISCONNECT receipt:close-1` then close
  the WebSocket; or just close the WebSocket and let the server clean up.

## Subscriptions

### `/topic/sites/{siteId|siteUid}/capacityChanged`

Both a numeric-`id` topic and a `siteUid` topic exist and the SPA subscribes
to **both**. But they are **not** equivalent (live-verified 2026-07-04):

- **Streaming measurement frames** (after `/app/streaming/start`) are pushed
  **only** on the **`siteUid`** topic (`/topic/sites/992179e1/capacityChanged`).
  A client subscribed only to the numeric-id topic receives nothing.
- **`capacityChanged` state-change events** were historically seen on the
  numeric-id topic; if in doubt, subscribe to both like the SPA does.

Note that `/app/streaming/start` (above) is stricter and requires the
**numeric** `siteId` in its JSON body.

Implementation in the bundle (chunk 866):

```js
i.current = n.subscribe(
  "/topic/sites/".concat(t.siteUid, "/capacityChanged"),
  e => { f.current && c(t => _a(JSON.parse(e.body), t)) }
);
```

Two payload shapes flow through this destination:

#### `capacityChanged` payload — relay state changes

JSON-serialized capacity that has just changed:

```json
{ "id": 48067, "enable": true, ... }
```

The UI uses it to flip the on/off pill of a relay tile without re-polling.

#### Streaming payload — live measurements

Once `/app/streaming/start` has been sent, frames carry:

```json
{
  "gatewayUid": "BX2A4B84F9",
  "measures": [
    {
      "capacityId": "AZUREIOT-co.9.instances.0.switch.0.data",
      "measureKind": "STATE",
      "value": "true"
    },
    {
      "capacityId": "AZUREIOT-co.2.instances.0.sensor.0.withdrawal.data",
      "measureKind": "FLOW",
      "value": "307.0"
    }
  ]
}
```

All numeric values are JSON **strings** (`"307.0"`, `"true"`) — clients
must parse. Frames with `measures: []` are gateway status pings; the
SPA ignores them.

The `capacityId` string here matches the `capacityId` field returned by
`/api/devices` and `/api/connectedobjects`, so the WS → entity mapping
can reuse the catalog already fetched via REST.

`capacityId` conventions for `AZUREIOT`-gatewayed capacities:

```
AZUREIOT-co.{coId}.instances.{phase}.switch.{n}.data            -> STATE  (on/off)
AZUREIOT-co.{coId}.instances.{phase}.sensor.{n}.withdrawal.data -> FLOW   (W from grid)
AZUREIOT-co.{coId}.instances.{phase}.sensor.{n}.injection.data  -> FLOW   (W to grid)
AZUREIOT-co.{coId}.instances.{phase}.sensor.{n}.production.data -> FLOW   (W from local source)
AZUREIOT-co.{coId}.instances.{phase}.sensor.{n}.consumption.data-> FLOW   (W per device clamp)
AZUREIOT-co.{coId}.instances.{phase}.sensor.{n}.data            -> FLOW   (W plain per-device clamp; live-observed)
```

### Frame cadence (observed)

Over a 2-minute listen on a residential three-phase site:

| `measureKind` | Seen? | Frames / 2 min | Meaning |
|---|---|---|---|
| `FLOW`     | ✅ | 480 | Live power per phase / per clamp (W). |
| `STATE`    | ✅ |  36 | Switch state (`"true"` / `"false"`) for `POWER_SWITCH` / `RELAY`. |
| `QUANTITY` | ❌ |   0 | Hourly energy buckets (Wh) — likely emitted only on bucket roll-over. |
| `VALUE`    | ❌ |   0 | Temperature (°C) — only present on sites with a thermal device. |
| `INDEX` / `RATE` | ❌ | 0 | Not observed in the window. |

That is sub-30-second updates per metered capacity — much finer than
the integration's 2-minute REST poll.

## What is NOT pushed

| Use case | Push? |
|---|---|
| Relay / pilot-wire / thermostat **state changed** | ✅ via `capacityChanged` |
| Live power per device (`FLOW`) | ✅ after `/app/streaming/start` |
| Switch state via streaming (`STATE`) | ✅ after `/app/streaming/start` |
| Battery state of charge | ❌ poll |
| Hourly energy (`QUANTITY`) on demand | ⚠️  emitted on bucket rollover only |
| EcoWatt / Tempo updates | ❌ poll |
| Topology changes (devices added) | ❌ poll `/api/devices` |

## Implications for the Python client and the HA integration

- **Replace the per-device polling for live power** with the streaming
  channel: open the WS once per site, subscribe, send `start`, and
  update the entity dict on every `MESSAGE`. REST poll drops to a slow
  fallback (~10 min) for `QUANTITY` rollovers and topology changes.
- **Switch state** can also flow through the stream (or via
  `capacityChanged`); polling becomes unnecessary for it.

## Security: broker tenant isolation issue

**The STOMP broker does not scope wildcard subscriptions to the
authenticated user.**

While probing, subscribing to:

```
/topic/**
/topic/#
```

(both valid RabbitMQ topic patterns) returned a firehose of
`capacityChanged` messages for **every** `siteUid` on the backend — 52
distinct sites in a 60-second window, none of which belong to the test
account. That is a tenant-isolation bug in the message-broker
authorization, not in the HTTP API.

**Responsible disclosure:** worth reporting privately to Comwatt
security. Do **not** use wildcard subscriptions in any production
client — always subscribe to exactly
`/topic/sites/{your_site_id}/capacityChanged`.

## Caveats

- All numeric values in frames are JSON **strings** (e.g. `"307.0"`,
  `"true"`). Clients must parse.
- Frames with `measures: []` are normal gateway status pings.
- The `message-id` header increments globally per connection, not per
  subscription.
- `SEND /app/streaming/start` must be reissued after every reconnect.
