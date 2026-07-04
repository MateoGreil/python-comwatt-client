# Tiles & dashboard

## `GET /api/tiles?siteId={siteId}`

Returns the configuration of every tile on the user's dashboard. **It is a
configuration endpoint, not a data endpoint** — it does **not** include
current power values, only "which tile of which type points at which
device".

Sample shape:

```jsonc
{
  "tileType": "REAL_TIME",     // REAL_TIME | VALUATION | THIRD_PARTY
  "id":       378561,
  "name":     "lave-linge",
  "position": 40,
  "hasChart": true,
  "chartType": "...",
  "site":     { ... },          // back-ref to the site
  "device":   { ... },          // full device payload (or @ref)
  "tileChartDatas": [ ... ]
}
```

`tileChartDatas` is the per-tile **chart configuration** — which
`measureKind` to plot, the colour/series settings, and (for `VALUATION`
tiles) the tariff/price metadata used to convert energy into euros.
It is configuration only; the actual time-series points still come from
`/api/aggregations/time-series` calls keyed by the tile's `device.id`.

On the test site (1 site, 20 devices) the endpoint returned **56 tiles**:
`{ REAL_TIME: 18, VALUATION: 37, THIRD_PARTY: 1 }`.

To get the actual values for each tile, the SPA then issues one
`/api/aggregations/time-series` call **per tile** (with the tile's `device.id`).
This is the chattiness the GitHub issue #40 is complaining about.

## Other tile endpoints

- `PUT /api/tiles/{tileId}` — update a tile (name, position, etc.)
- `POST /api/tiles` — create
- `DELETE /api/tiles/{tileId}` — remove
