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

## `GET /api/sites/{siteId}`

Returns a single site by its numeric ID. Response shape is identical to a single entry from `GET /api/sites`.

- **200** with the site object when it exists.
- **500** when the ID does not exist (not 404 — live 2026-11-14).

Dead variants (do not re-probe):
- `GET /api/sites/by-uid/{uid}` → 404 "No static resource"
- `GET /api/sites/{siteUid}` (UID in numeric path position) → 400 "Failed to convert 'siteId'"
- Query parameters `?siteId=...` or `?siteUid=...` on `GET /api/sites` are ignored (returns full list)

## `GET /api/sites/by-site-uid/{siteUid}`

Returns a single site by its short `siteUid` string (e.g. "abc12345"). Response shape is identical to the entries from `GET /api/sites`.

- **200** with the site object when it exists.
- **500** when the UID does not exist (not 404 — live 2026-11-14).

## `GET /api/sites/{siteId}/profile`

Referenced by the SPA but returns **403** for a normal end-user. Likely an
installer/admin-only endpoint.

## Site administration

Single-site reads live-verified 2026-10-11; write paths from the SPA
bundle, not exercised.

- `GET  /api/sites/{id}` — **200**, the single site; same key set as the
  entries of `GET /api/sites` (nested values can differ).
- `GET  /api/sites/by-site-uid/{siteUid}` — **200**; payload identical to
  `GET /api/sites/{id}` (compared live 2026-10-11).
- `GET  /api/sites/{siteId}/gateways/{gatewayUid}` — one gateway of the
  site.
- `PUT  /api/sites/{id}/gateways/{gatewayUid}` — assign that gateway to
  the site (installer flow).
- `PUT  /api/sites/{siteUid}/reloadConnexionStatus` — ask the site's
  gateway(s) to re-report their connection status. Mind the id: this one
  takes the **`siteUid`**, not the numeric `id` (same trap family as the
  gateway two-ids table in [`devices.md`](devices.md#gateways)).
- `PUT  /api/sites/{id}/send-installation-progress` — installer
  installation-progress notification.
- `POST /api/sites/transfer/installForUser` — initiate a site transfer to
  another user.
- `GET  /api/sites/transfer/{id}/target-user-information` — target user
  of a pending transfer. **404** outside a pending transfer
  (live-verified 2026-10-11) — body is the bare-array format, but
  degenerate: a single entry with `codes: []` and `code: null`, no
  message at all (see
  [error conventions](README.md#error--status-code-conventions)).

## Other site-scoped endpoints (referenced from the bundle)

- `GET  /api/sites/{siteId}/gateway-addability?gatewayUid={GATEWAY_UID}`
- `POST /api/sites/add`, `POST /api/sites/add/installer`,
  `POST /api/sites/add/installer/devices`,
  `POST /api/sites/add/installer/form` — the "create a new site" wizard.

## Users

- `GET  /api/users/authenticated` (see [`auth.md`](auth.md))
- `GET  /api/delegatedaccess`, `* /api/delegatedaccess/{id}` — delegated access
  management between accounts (e.g. installer ↔ end-user).

### Account lifecycle (`/api/users`)

From the SPA bundle (2026-09 re-exploration); reads live-verified 2026-10-11,
write paths not exercised.

- `POST /api/users/` — register a new account.
- `PUT  /api/users/{id}` / `DELETE /api/users/{id}` — update / delete the
  account.
- `PUT  /api/users/{id}/updateemail` — change the account email.
- `POST /api/users/{email}/forgottenpasswd` — send the password-reset mail.
- `PUT  /api/users/{email}/forgottenpasswd/{token}` — complete the reset;
  body `{"password": <salted sha256>}` (same hash recipe as login, see
  [`auth.md`](auth.md)).
- `PUT  /api/users/{email}/token/{token}` — activation, token from the
  activation mail.
- `GET  /api/users/{email}/isReadyForSiteInstallation` — installer-side
  check; `403` for `END_USER` (live-verified 2026-10-11), body in the
  bare-array error format with `not authorized` (see
  [error conventions](README.md#error--status-code-conventions)).

> ⚠ **`GET /api/users/{id}/refreshtoken` is not a session refresh.** It
> re-sends the **activation mail**. On an already-activated account it
> fails with `412` + bare array `user.already.activated` (live-verified
> 2026-10-11 — the canonical example in the
> [error conventions](README.md#error--status-code-conventions)). Nothing
> here extends the `cwt_session` cookie; its lifetime is fixed at login.
