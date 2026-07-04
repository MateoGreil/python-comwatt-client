# Measure keys — the per-site measurement inventory

## `GET /api/measurekeys/measurekeys?siteId={siteId}`

Returns every distinct measurement available on the site, with a stable
UUID (`measureKey`), the `measureKind`, and the device the measurement
belongs to. 29 entries on the test account (1 site, 20 devices).

Sample entry:

```jsonc
{
  "@class": "MeasureKey",
  "id": 76076,
  "measureKind": "FLOW",
  "measureType": {
    "code": "ELECTRICITY",
    "measureKinds": ["STATE", "FLOW", "QUANTITY"]
  },
  "measureKey": "c0a36626-886e-4fd5-a913-3e87cafecee9",
  "shared": false,
  "device": {
    "id": 23593,
    "name": "solaire en autoproduction",
    "deviceKind": { "code": "SOLAR_PANEL", "category": "SOLAR_PRODUCTION" },
    "features": [ ... ]
  }
}
```

## What this is — and isn't — useful for

- ✅ A **flat catalog** of every (device, measureKind) pair on the site,
  in one call. Handy for building an entity catalog (HA integration) or
  enumerating every metric without walking the
  device → features → capacities tree from `/api/devices`.
- ✅ Stable identifiers (`id` + `measureKey` UUID) per measurement —
  useful keys for caching, mapping to entity unique-IDs, etc.
- ❌ **Not** a value endpoint — there is no `value` / `lastValue` field,
  only metadata.
- ❌ The `measureKey` UUID **does not** appear to be accepted by the
  `/api/aggregations/*` endpoints — those keep using numeric `id`s
  (device id for per-device series, site id for site series).

## How the SPA uses it

The dashboard fetches it once on site load to know which entities to
present, then issues per-device aggregation calls keyed by the numeric
`device.id`. The HA integration could similarly use it to decide which
entities to materialise without re-walking the much larger
`/api/devices` payload.
