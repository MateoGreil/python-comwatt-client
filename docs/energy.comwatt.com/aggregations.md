# Aggregations — the time-series API

This is the only family of endpoints that returns measurement data, and it
is the main thing the Python client and the Home Assistant integration call.

There are **three** endpoints, all under `/api/aggregations/`. The query
string is built by a single helper in the SPA bundle (`98769:F` in
`main.b0ddfab7.js`), reproduced below verbatim:

```js
function F(e){
  let { id:t, scale:n, measureKind:r,
        aggregationLevel:i = T(n),
        aggregationType:o,
        siteNetworkType:a,
        start:u,
        from:d = null,
        timeAgoUnit:h = ( s().existy(u) ? null : n ),
        timeAgoValue:p = ( s().existy(h) ? "1" : null )
      } = e;
  let m = false;
  if ("DAY" === n) {
    m = L( ("undefined"===typeof d || null===d) ? c.c9.local() : d,
           null===u ? undefined : u );
    m && (i = "HOUR");
  }
  return (0, l.n)([
    ["id",                t],
    ["measureKind",       r],
    ["aggregationLevel",  i],
    ["aggregationType",   o],
    ["siteNetworkType",   a],
    ["timeAgoUnit",       h],
    ["timeAgoValue",      p],
    ["start",             u ? (0, f.OY)(u) : null ],
    ["end",               (0, f.OY)( d || c.c9.local() ) ],
  ]);
}
```

Take-aways from the helper:

- The wire-level parameter is **`aggregationLevel`** — what the SPA calls
  `scale` in the JS layer maps to it. The backend **requires** `aggregationLevel`
  on every call (confirmed: requests without it return
  `400 "Required parameter 'aggregationLevel' is not present"`).
- You can address a time range with **either** `timeAgoUnit`+`timeAgoValue`
  **or** `start`+`end`. If you pass `timeAgoUnit`, the backend computes the
  range from "now". If you pass `start`/`end` (ISO-8601, with `Z`), they
  override the time-ago params (the helper would set them to `null`).
- `end` always defaults to "now" client-side, even when not passed by the
  caller. The backend itself also defaults `end` to "now" if absent.

## Enums (collected from the bundle and the responses)

| Param | Values seen |
|---|---|
| `measureKind` | `FLOW` (instantaneous power, W), `QUANTITY` (energy, Wh), `STATE` (relay/contactor on/off), `VALUE` (e.g. temperature °C), `INDEX` (cumulative meter index), `RATE` (ratio, e.g. self-consumption %) |
| `aggregationLevel` | `NONE`, `HOUR`, `DAY`, `WEEK`, `MONTH`, `YEAR` (the SPA also uses `scale` with the same values; mapping `HOUR→NONE`, `WEEK→HOUR`, `MONTH→DAY`, `YEAR→MONTH`) |
| `aggregationType` | `NONE`, `MIN`, `MAX`, `SUM`, `AVERAGE` |
| `siteNetworkType` | `CONSUMPTION`, `INJECTION`, `WITHDRAWAL`, `PRODUCTION` (all live-verified `200`). `BATTERY` is **rejected** (`400 "Failed to convert 'siteNetworkType' with value: 'BATTERY'"`) despite `site-time-series` exposing `charges`/`discharges` — there is no battery `siteNetworkType`. |
| `timeAgoUnit` | same as `aggregationLevel` |
| `timeAgoValue` | integer as a string, default `"1"` |

## 1. `GET /api/aggregations/time-series`

Per-device time series.

```
GET /api/aggregations/time-series
    ?id={deviceId}
    &measureKind=FLOW
    &aggregationLevel=HOUR
    &aggregationType=NONE        # or MAX / MIN / SUM
    &timeAgoUnit=DAY
    &timeAgoValue=1
```

Response:

```json
{
  "timestamps": ["2026-04-23T19:00:00Z", "..."],
  "values":     [16246.0, 18672.0, ...]   // unit depends on measureKind
}
```

### Multi-id behaviour (important for issue #40)

The backend accepts the `id` parameter **multiple times**:

```
?id=23593&id=23597&id=23600&...
```

When you do that, the extra `id` params are **ignored** — the response is
just the **first** id's series, returned with a single `values` array. It is
neither a sum nor a per-device breakdown. Live-verified as order-dependent:
`?id=A&id=B` returns A's series, `?id=B&id=A` returns B's series (identical
to the single-id call for that first device). So repeated `id=` **cannot** be
used to fetch or sum several devices in one call — there is no REST
bulk-per-device or bulk-sum shortcut.

> ⚠ **Correction (2026-07-04).** An earlier version of this note claimed the
> multi-`id` response was the *sum* of the requested devices. That is wrong:
> re-testing against the live backend shows only the first `id` is honoured.

`id=A,B` (comma-separated) is rejected:
`400 "Failed to convert 'id' with value: '...,...'"`. So it really has to be
repeated query params.

### `siteNetworkType` overload

Same endpoint, but addressed at the site instead of a device, with
`siteNetworkType` instead of `aggregationLevel`-only:

```
GET /api/aggregations/time-series
    ?id={siteId}
    &measureKind=FLOW
    &aggregationLevel=HOUR
    &aggregationType=NONE
    &siteNetworkType=CONSUMPTION   # or INJECTION / WITHDRAWAL / ...
    &timeAgoUnit=DAY&timeAgoValue=1
```

Returns the same `{timestamps, values}` shape but for the chosen virtual
"network" of the site.

## 2. `GET /api/aggregations/site-time-series` ★ recommended

The whole-site rollup, in **one** call. This is what the dashboard uses.

```
GET /api/aggregations/site-time-series
    ?id={siteId}
    &measureKind=FLOW              # or QUANTITY
    &aggregationLevel=HOUR
    &aggregationType=NONE
    &timeAgoUnit=DAY&timeAgoValue=1
```

Response — **12 series sharing one timestamps axis** (live-verified
2026-07-04):

```json
{
  "timestamps":           [ "2026-04-23T18:00:00Z", ...],
  "productions":          [ ... ],
  "consumptions":         [ ... ],
  "injections":           [ ... ],
  "withdrawals":          [ ... ],
  "charges":              [ ... ],   // battery charge
  "discharges":           [ ... ],   // battery discharge
  "autoproductionRates":  [ ... ],
  "autoconsumptionRates": [ ... ],
  "injectionRates":       [ ... ],
  "withdrawalRates":      [ ... ],
  "chargeRates":          [ ... ],   // battery charge rate
  "dischargeRates":       [ ... ]    // battery discharge rate
}
```

A site without a battery still has the `charges` / `discharges` keys (empty
or zero series).

This single endpoint is the current spelling of the older
`/api/aggregations/site-networks-ts-time-ago` that the Python client wraps
today. **The legacy endpoint is not removed** — it still returns `200` with
the same response shape (re-verified 2026-07-04); the SPA simply moved to
`site-time-series`. (Commit `e0dbcd9 🔥 Replace removed API endpoint` actually
swapped the *per-device* `device-ts-time-ago` for `time-series`, not this
site-level one — and `device-ts-time-ago` currently responds `200` again
too.) For a "whole site at a glance" use case it is still **strictly better
than 4–6 parallel calls**.

## 3. `GET /api/aggregations/top-consumption`

Per-device consumption percentages for a site, in one call. No timestamps,
no absolute values. The server **caps the result at the top 5** and lumps
the remainder under an `"others"` bucket.

```
GET /api/aggregations/top-consumption
    ?id={siteId}
    &aggregationLevel=DAY
    &timeAgoUnit=DAY&timeAgoValue=1
```

Response:

```json
{
  "elements": [
    { "label": "voiture électrique",        "percentageValue": 34 },
    { "label": "piscine",                   "percentageValue": 30 },
    { "label": "chauffe-eau thermodynamique","percentageValue": 29 },
    { "label": "CAVE",                      "percentageValue": 21 },
    { "label": "congélateur bureau",        "percentageValue": 18 },
    { "label": "others",                    "percentageValue": 68 }
  ]
}
```

This is the current spelling of the older
`/api/aggregations/consumption-breakdown-time-ago` that is still wrapped by
`ComwattClient.get_site_consumption_breakdown_time_ago`. **The legacy
endpoint is not removed** — it still returns `200` with the same `elements`
shape (re-verified 2026-07-04). Migrating to `top-consumption` is about
tracking the SPA, not fixing breakage.

## 4. Legacy: `GET /api/aggregations/site-networks-ts-time-ago`

The previous spelling of `site-time-series`. Same query string but indexed
by `siteId=` (not `id=`), same response shape. **Still live (`200`,
re-verified 2026-07-04)** — not removed. The Python client still wraps it;
migrate to `site-time-series` when convenient.

The sibling legacy endpoints `consumption-breakdown-time-ago` and the
per-device `device-ts-time-ago` also still return `200` today.

## What was tried and does NOT exist

Probed and got **404** from the same Spring backend (so they really aren't
mounted under the current API):

```
/api/aggregations/devices-time-series
/api/aggregations/multi-time-series
/api/aggregations/time-series/multi
/api/aggregations/devices-ts-time-ago
/api/aggregations/bulk-time-series
/api/aggregations/time-series-bulk
```

`?ids=...` and `?deviceIds=...` (as alternatives to repeated `id`) both fail
with `400 "Required parameter 'id' is not present"`.

## Live-verified examples

```
GET /api/aggregations/time-series
    ?id=23593&measureKind=FLOW&aggregationLevel=HOUR
    &aggregationType=NONE&timeAgoUnit=DAY&timeAgoValue=1
→ 200 {"timestamps": [...], "values": [16246.0, 18672.0, ...]}

GET /api/aggregations/site-time-series
    ?id=3349&measureKind=FLOW&aggregationLevel=HOUR
    &aggregationType=NONE&timeAgoUnit=DAY&timeAgoValue=1
→ 200 {"timestamps":[...], "productions":[...], "consumptions":[...], ...}

GET /api/aggregations/top-consumption
    ?id=3349&aggregationLevel=DAY&timeAgoUnit=DAY&timeAgoValue=1
→ 200 {"elements":[{"label":"...", "percentageValue": ...}, ...]}
```
