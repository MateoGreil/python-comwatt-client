from __future__ import annotations

import json
import random
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from ._core import _BaseClient
from .exceptions import ComwattAuthError, ComwattStreamingError

_WS_URL = "wss://frontage.energy.comwatt.com/ws"
_STREAM_EXTRA_MESSAGE = (
    "WebSocket streaming requires the 'stream' extra: pip install comwatt-client[stream]"
)


def _encode_frame(command: str, headers: dict[str, str], body: str = "") -> str:
    header_block = "".join(f"{key}:{value}\n" for key, value in headers.items())
    return f"{command}\n{header_block}\n{body}\x00"


def _parse_frame(text: str) -> tuple[str, dict[str, str], str]:
    if text.endswith("\x00"):
        text = text[:-1]
    first_nl = text.find("\n")
    if first_nl == -1:
        return text, {}, ""
    command = text[:first_nl]
    rest = text[first_nl + 1:]
    sep = rest.find("\n\n")
    if sep == -1:
        header_block = rest
        body = ""
    else:
        header_block = rest[:sep]
        body = rest[sep + 2:]
    headers: dict[str, str] = {}
    for line in header_block.split("\n"):
        if not line:
            continue
        key, _, value = line.partition(":")
        headers[key] = value
    return command, headers, body


def _open_websocket(cookie: str, timeout: float) -> Any:
    import websocket

    return websocket.create_connection(
        _WS_URL,
        timeout=timeout,
        header=[f"Cookie: cwt_session={cookie}"],
    )


def _try_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _try_bool(value: Any) -> bool | None:
    if value == "true":
        return True
    if value == "false":
        return False
    return None


@dataclass(frozen=True)
class Measurement:
    gateway_uid: str
    capacity_id: str
    measure_kind: str
    value: str
    value_float: float | None
    value_bool: bool | None

    @classmethod
    def from_measure(cls, gateway_uid: str, measure: dict[str, Any]) -> Measurement:
        value = measure["value"]
        return cls(
            gateway_uid=gateway_uid,
            capacity_id=measure["capacityId"],
            measure_kind=measure["measureKind"],
            value=value,
            value_float=_try_float(value),
            value_bool=_try_bool(value),
        )


@dataclass(frozen=True)
class CapacityChanged:
    """Notification that a site capacity's configuration changed.

    The dataclass is frozen so field references cannot be reassigned, but
    ``raw`` holds the underlying payload dict and is not deeply immutable —
    callers must not mutate its contents.
    """

    capacity_id: int
    enable: bool | None
    raw: dict[str, Any]


def _close_ws(ws: Any) -> None:
    try:
        ws.send(_encode_frame("DISCONNECT", {}))
    except Exception:
        pass
    try:
        ws.close()
    except Exception:
        pass


def _consume_stream(ws: Any, ws_closed_exc: type[BaseException]) -> Iterator[Measurement | CapacityChanged]:
    while True:
        try:
            frame = ws.recv()
        except ws_closed_exc:
            break
        if not frame:
            break
        command, _, body = _parse_frame(frame)
        if command != "MESSAGE":
            continue
        try:
            payload = json.loads(body)
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        if "measures" in payload:
            gateway_uid = payload["gatewayUid"]
            for measure in payload["measures"]:
                yield Measurement.from_measure(gateway_uid, measure)
        elif "id" in payload:
            yield CapacityChanged(
                capacity_id=payload["id"],
                enable=payload.get("enable"),
                raw=payload,
            )


class StreamingMixin(_BaseClient):
    def _connect_and_start(
        self, site_id: int, site_uid: str
    ) -> tuple[Any, type[BaseException]]:
        try:
            import websocket as _websocket
        except ImportError:
            raise ComwattStreamingError(_STREAM_EXTRA_MESSAGE) from None

        ws_closed_exc = _websocket.WebSocketConnectionClosedException
        cookie = self.session.cookies.get("cwt_session") or ""

        try:
            ws = _open_websocket(cookie, self.timeout)
        except ImportError:
            raise ComwattStreamingError(_STREAM_EXTRA_MESSAGE) from None
        except _websocket.WebSocketBadStatusException as exc:
            if exc.status_code in (401, 403):
                if self.auto_reauth and self._username and self._auth_hash:
                    self._reauthenticate()
                    new_cookie = self.session.cookies.get("cwt_session")
                    if new_cookie is None:
                        raise ComwattAuthError(
                            "Re-authentication did not set a new session cookie"
                        )
                    try:
                        ws = _open_websocket(new_cookie, self.timeout)
                    except _websocket.WebSocketBadStatusException as inner_exc:
                        raise ComwattAuthError(
                            "Authentication rejected by streaming endpoint"
                        ) from inner_exc
                    except _websocket.WebSocketException as inner_exc:
                        raise ComwattStreamingError(
                            f"WebSocket connection failed: {inner_exc}"
                        ) from inner_exc
                else:
                    raise ComwattAuthError(
                        "Authentication rejected by streaming endpoint"
                    ) from exc
            else:
                raise ComwattStreamingError(
                    f"WebSocket connection failed: {exc}"
                ) from exc
        except _websocket.WebSocketException as exc:
            raise ComwattStreamingError(f"WebSocket connection failed: {exc}") from exc

        try:
            ws.send(
                _encode_frame(
                    "CONNECT",
                    {"accept-version": "1.1,1.2", "heart-beat": "10000,10000"},
                )
            )
            command, _, _ = _parse_frame(ws.recv())
            if command != "CONNECTED":
                raise ComwattStreamingError(
                    f"STOMP handshake failed: expected CONNECTED, got {command!r}"
                )
            ws.send(
                _encode_frame(
                    "SUBSCRIBE",
                    {
                        "id": "sub-0",
                        "destination": f"/topic/sites/{site_uid}/capacityChanged",
                        "ack": "auto",
                    },
                )
            )
            ws.send(
                _encode_frame(
                    "SEND",
                    {"destination": "/app/streaming/start", "content-type": "application/json"},
                    body=json.dumps({"siteId": site_id}),
                )
            )
        except (ComwattStreamingError, ComwattAuthError):
            _close_ws(ws)
            raise
        except _websocket.WebSocketException as exc:
            _close_ws(ws)
            raise ComwattStreamingError(
                f"WebSocket connection failed during STOMP handshake: {exc}"
            ) from exc

        return ws, ws_closed_exc

    def stream_measurements(
        self,
        site: dict[str, Any],
        *,
        reconnect: bool = False,
        reconnect_backoff: float = 1.0,
        reconnect_backoff_max: float = 60.0,
        reconnect_max_attempts: int | None = None,
    ) -> Iterator[Measurement | CapacityChanged]:
        if "siteUid" not in site:
            raise ValueError("site dict is missing required key 'siteUid'")
        if "id" not in site:
            raise ValueError("site dict is missing required key 'id'")
        cookie = self.session.cookies.get("cwt_session")
        if not cookie:
            raise ComwattAuthError("Not authenticated: no cwt_session cookie")
        site_id = site["id"]
        site_uid = site["siteUid"]

        if not reconnect:
            ws, closed = self._connect_and_start(site_id, site_uid)
            try:
                yield from _consume_stream(ws, closed)
            finally:
                _close_ws(ws)
            return

        attempts = 0
        delay = reconnect_backoff
        while True:
            try:
                ws, closed = self._connect_and_start(site_id, site_uid)
            except ComwattAuthError:
                raise
            except ComwattStreamingError as exc:
                attempts += 1
                if reconnect_max_attempts is not None and attempts >= reconnect_max_attempts:
                    raise ComwattStreamingError(
                        f"giving up after {attempts} reconnect attempts"
                    ) from exc
                time.sleep(random.uniform(0, delay))
                delay = min(delay * 2, reconnect_backoff_max)
                continue

            attempts = 0
            delay = reconnect_backoff
            try:
                yield from _consume_stream(ws, closed)
            finally:
                _close_ws(ws)
