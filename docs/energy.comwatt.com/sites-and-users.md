# Sites & users

## `GET /api/sites`

Returns every site the authenticated user has access to. Array of:

```
id, name, description, createDate, updateDate, ownerAssignDate,
threePhase (bool),
address{ address, postalCode, city, country },
currency, language, metric,
siteUid,                # the short UUID-like id you see in the URL hash (e.g. "992179e1")
supplyNumber,           # PRM / PDL number for the meter
siteKind,               # e.g. RESIDENTIAL
owner{ id, uuid, login, firstName, lastName, email, profile{...},
       phone, mobilePhone },
gateways[ {
  id, gatewayUid (e.g. "BXCCBB77D9"),
  status,               # e.g. ASSIGNED_END_USER
  connectedObjectReference{ id, coProductUid, coType, ... },
  ...
} ],
state, status,          # site lifecycle / status (added since 2026-04; live 2026-07-04)
informationSource,      # provenance of the site record
product,                # Comwatt product bound to the site
accessType              # e.g. present when access is delegated
```

> Fields `state`, `status`, `informationSource`, `product` and `accessType`
> were **not** in the 2026-04 capture but are returned by the live API on
> 2026-07-04 — the payload has grown; treat the field list as non-exhaustive.

Notes:

- `id` is the **internal numeric id** used by every other endpoint that takes
  a `siteId` query param.
- `siteUid` is the **short id** used in the SPA URL (`#/sites/<siteUid>/...`)
  and by a couple of "by-site-uid" endpoints (`/api/devicekinds/by-site-uid/{siteUid}`,
  STOMP topic `/topic/sites/{siteUid}/capacityChanged`).

Both ids exist in the response, so the client can pick whichever it needs.

## `GET /api/sites/{siteId}/profile`

Referenced by the SPA but returns **403** for a normal end-user. Likely an
installer/admin-only endpoint.

## Other site-scoped endpoints (referenced from the bundle)

- `GET  /api/sites/{siteId}/gateways/{gatewayUid}`
- `GET  /api/sites/{siteId}/gateway-addability?gatewayUid={GATEWAY_UID}`
- `POST /api/sites/add`, `POST /api/sites/add/installer`,
  `POST /api/sites/add/installer/devices`,
  `POST /api/sites/add/installer/form` — the "create a new site" wizard.

## Users

- `GET  /api/users/authenticated` (see [`auth.md`](auth.md))
- `*    /api/users` and sub-resources (referenced; not exercised here — likely
  used for profile editing)
- `GET  /api/delegatedaccess`, `* /api/delegatedaccess/{id}` — delegated access
  management between accounts (e.g. installer ↔ end-user).
