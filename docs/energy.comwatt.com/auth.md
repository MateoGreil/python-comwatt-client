# Auth

## End-to-end flow

1. **Login** — `POST /api/v1/authent` with the salted SHA-256 hash of the
   password (recipe below). The 200 response is empty; the session is in
   the `Set-Cookie: cwt_session=...` header.
2. **Persist the cookie** — store it in a cookie jar (browsers do this
   automatically; Python clients use `requests.Session` /
   `httpx.AsyncClient`).
3. **Use the cookie everywhere** — every subsequent HTTP call sends it as
   `Cookie: cwt_session=...`. The same cookie authenticates the
   WebSocket handshake at `wss://frontage.energy.comwatt.com/ws` (see
   [`websocket-realtime.md`](websocket-realtime.md)) — no extra token.
4. **Detect expiry** — any endpoint returns `401` once the cookie is
   rejected. The cheapest probe is `GET /api/users/authenticated`; treat
   `401`/`403` as "re-login required".
5. **Logout** — `POST /api/v1/logout` invalidates the cookie server-side.

## Login

`POST /api/v1/authent`

Request:

```http
POST /api/v1/authent HTTP/1.1
Content-Type: application/json

{
  "username": "<email>",
  "password": "<sha256_hex>"
}
```

`<sha256_hex>` is computed as:

```python
hashlib.sha256(f"jbjaonfusor_{password}_4acuttbuik9".encode()).hexdigest()
```

Hard-coded prefix/suffix come from the SPA bundle (and are also already used
by `comwatt_client/_auth.py`).

Response:

- **200 OK**, empty body. The session is established via the `Set-Cookie`
  header.
- **4xx** with an RFC-7807 `application/problem+json` body on failure.

## The session cookie

Cookie name: **`cwt_session`**

Properties observed:

- `Domain=.energy.comwatt.com`
- `Path=/`
- `Secure` (HTTPS-only)
- (effectively) `HttpOnly` — set by the server, browser sends it with every
  request to the API; the JS bundle never reads it
- Lifetime is a session/long-lived cookie; the server may rotate it
- The value is a **JWE** (encrypted JWT) with header
  `{"cty":"JWT","enc":"A128GCM","alg":"dir"}` — the payload is opaque to the
  client

The same cookie is reused for the **WebSocket** handshake at
`wss://frontage.energy.comwatt.com/ws` (see `websocket-realtime.md`).

## Logout

`POST /api/v1/logout` (referenced from the bundle). Invalidates the cookie
server-side. Body is empty.

## Authenticated user

`GET /api/users/authenticated`

Returns the current user document. Confirmed fields:

```
@id, id, login, firstName, lastName, informationSource, email, newEmail,
pseudonym, profile{ id, label, code, authorities[], globalProfile,
supervisor, installer, endUser, admin, wattInside, datascience, support,
coach },
address, phone, mobilePhone, currency, language, activated, deleted,
company, createDate, updateDate, agreements[], uuid
```

Useful as a "ping" to verify the cookie is still valid (returns 401/403 if
not).
