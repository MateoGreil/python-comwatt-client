# energy.comwatt.com — API field notes

> 🤖 **AI-generated documentation.** This entire directory was produced by
> AI agents (Claude) reverse-engineering the Comwatt web app — both the
> exploration (reading the JS bundle, probing endpoints, sniffing the
> WebSocket) and the writing. It was reviewed by a second AI agent and
> spot-checked by a human, but it is **not** official Comwatt
> documentation. Treat it as "best-effort, correct as of the date below"
> and verify anything load-bearing against the live API before relying
> on it.

Reverse-engineered notes on the HTTP/WebSocket API used by the Comwatt
"Mon Energie" web app at <https://energy.comwatt.com>. The web UI is a React
SPA that talks to a Spring Boot backend behind nginx; there is **no public
OpenAPI / Swagger / Actuator**, so everything here was reconstructed from:

- the JavaScript bundle (`/static/js/main.*.js` + 5 lazy chunks),
- live HTTP / WebSocket calls authenticated as a normal end-user,
- the existing Python client in this repo.

> Discovered against the production frontend on 2026-04-24 with bundle
> `main.b0ddfab7.js`. URLs and payloads can change without notice.
>
> **Re-verified live on 2026-07-04** (bundle `main.cec7aaba.js`). Corrections
> from that pass are folded in: repeated `id=` returns only the **first** id
> (not a sum), the `*-time-ago` endpoints still respond **200** (not removed),
> `site-time-series` returns **12** series, `siteNetworkType` accepts
> `PRODUCTION` (and rejects `BATTERY`), and the WebSocket measurement stream
> is delivered on the **`siteUid`** topic (confirmed working live).

## Summary

What this directory documents, in one paragraph: the Comwatt API is a
cookie-authenticated JSON HTTP API plus a STOMP-over-WebSocket channel.
Login at `POST /api/v1/authent` returns a `cwt_session` JWE cookie that
authenticates every subsequent HTTP and WebSocket call. Resources are
organised around **sites** → **devices** → **capacities** (the atomic
sensors / actuators). Time-series data comes from three
`/api/aggregations/*` endpoints — one per device, one for the whole
site at once, one for the top-N consumption breakdown. Actuators
(relays, pilot wires, thermostats) are switched via
`PUT /api/capacities/{id}/...`. Live measurements (power per phase,
relay state, …) are pushed over WebSocket once the client sends
`SEND /app/streaming/start`. There is also a security finding about the
broker leaking other tenants' data on wildcard subscriptions.

## Conventions

- **Base URL:** `https://energy.comwatt.com/api`
- **WebSocket URL:** `wss://frontage.energy.comwatt.com/ws`
- **Transport:** HTTPS, JSON in/out, Spring's RFC-7807 `application/problem+json`
  on errors.
- **Auth:** session cookie `cwt_session` (a JWE — encrypted JWT, alg `dir`,
  enc `A128GCM`). Set after `POST /api/v1/authent`. Sent automatically by the
  browser; the Python client uses a `requests.Session` for the same effect.
  The same cookie authenticates the WebSocket handshake.
- **No CSRF token** is required for the JSON endpoints in normal browser flows
  (same-site cookie + JSON content-type is enough).
- **Discovery probes that returned 404** (sanity): `/api/swagger`,
  `/api/swagger-ui.html`, `/api/v3/api-docs`, `/api/openapi.json`,
  `/api/actuator/*`, `/api/management/*`, `/robots.txt`, `/sitemap.xml`.
  → No machine-readable schema is exposed.

## Files in this directory

| File | What's in it |
| --- | --- |
| [`auth.md`](auth.md) | Login, logout, the password-hash scheme, the `cwt_session` JWE. |
| [`sites-and-users.md`](sites-and-users.md) | `/api/users/authenticated`, `/api/sites`, site profile, delegated access. |
| [`devices.md`](devices.md) | `/api/devices`, `/api/connectedobjects`, device kinds, capacities (sensors / relays). |
| [`measurekeys.md`](measurekeys.md) | `/api/measurekeys/measurekeys` — the per-site measure inventory. |
| [`aggregations.md`](aggregations.md) | The time-series API (per-device, per-site-network, whole-site, top-consumption) — **read this for issue #40**. |
| [`capacities.md`](capacities.md) | Switching relays, pilot-wire, thermostat set-points. |
| [`tiles-and-dashboard.md`](tiles-and-dashboard.md) | The dashboard configuration endpoint and what it does (and does not) return. |
| [`misc-endpoints.md`](misc-endpoints.md) | Tempo / EcoWatt / device-kinds / connected objects / gateways / electricity contracts / plannings / typical days / alerts / thermal control / etc. |
| [`websocket-realtime.md`](websocket-realtime.md) | The STOMP-over-WebSocket channel — `capacityChanged` events **and** the live measurement stream activated by `/app/streaming/start`. |

## Gotchas (read before writing a client)

A handful of things that bite implementors and aren't obvious from any
single endpoint:

- **Two ids per site.** `id` is the numeric primary key (used by every
  query param like `?siteId=...`). `siteUid` is the short string in the
  URL hash (`#/sites/992179e1`) and in some `by-site-uid` paths and the
  STOMP topic. Both are returned by `/api/sites`.
- **Two ids per capacity.** `id` is the numeric primary key — **all
  `/api/capacities/{id}/...` URLs take this one**. `capacityId` is an
  opaque string (`"AZUREIOT-co.X.instances.Y..."`) used by the gateway
  and echoed in WebSocket streaming frames. Same field name, different
  things — see [`devices.md`](devices.md) and
  [`capacities.md`](capacities.md).
- **JSON-with-refs on `/api/devices`.** First occurrence carries
  `"@id": "N"`; later occurrences are `{"@ref": "N"}`. Tree walkers
  must resolve refs.
- **All numeric values in WebSocket frames are JSON strings**
  (`"307.0"`, `"true"`). Clients must parse.
- **`aggregationLevel` is mandatory** on every aggregations endpoint
  (omitting it returns 400). The SPA uses `scale` internally, but the
  wire param is `aggregationLevel`.
- **`?id=A&id=B&id=C` on `/api/aggregations/time-series` returns only the
  FIRST id's series** (order-dependent; not a sum, not per-device).
  Comma-separated `?id=A,B` is rejected.
- **`/api/plannings/?siteId=...` returns 404 on an empty list** — that
  is Spring's default for empty result sets, not a missing endpoint.

## Conventions for non-trivial requests

- **Content-type** for `POST` / `PUT` bodies is `application/json`.
- **Pagination**, where it exists, uses `?page={n}` (e.g.
  `delegatedaccess`, `plannings`, `typicaldays`). No `Link` header was
  observed; clients must keep incrementing until an empty page.
- **Rate limits**: no `X-RateLimit-*` headers were observed on any
  endpoint during exploration. The SPA fans out aggressively (React
  Query `useQueries`) without throttling, so any limits are likely
  generous — but treat this as anecdote, not contract.

## Error / status-code conventions

Spring Boot RFC-7807 problem+json shape on errors:

```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "Required parameter 'id' is not present.",
  "instance": "/api/aggregations/site-time-series"
}
```

Typical codes observed:

- `200` — success (JSON body; sometimes empty string for no-content).
- `400` — missing/invalid params.
- `401` — session expired (cookie rejected).
- `403` — role-forbidden endpoint (back-office, gateway-by-uid, site profile).
- `404` — malformed path **or** "no result" for some endpoints
  (`/plannings/?siteId=` returns 404 on an empty list — Spring's default
  behaviour, not a missing endpoint).
