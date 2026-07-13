import json

import pytest
import websocket as ws_lib

from comwatt_client import ComwattAuthError, ComwattStreamingError
from comwatt_client._streaming import (
    CapacityChanged,
    Measurement,
    _WS_URL,
    _encode_frame,
    _open_websocket,
    _parse_frame,
)

SITE = {"id": 12345, "siteUid": "BX"}

CONNECTED_FRAME = "CONNECTED\nversion:1.2\nheart-beat:0,0\n\n\x00"
MEASURES_FRAME = (
    "MESSAGE\nmessage-id:m-1\ndestination:/topic/sites/BX/capacityChanged\n\n"
    '{"gatewayUid":"BX","measures":'
    '[{"capacityId":"co.1.sensor.0.data","measureKind":"FLOW","value":"307.0"}'
    "]}\x00"
)
PING_FRAME = 'MESSAGE\nmessage-id:m-2\n\n{"gatewayUid":"BX","measures":[]}\x00'
CAPACITY_FRAME = 'MESSAGE\nmessage-id:m-3\n\n{"id":48067,"enable":true}\x00'


class FakeWS:
    def __init__(self, frames):
        self.sent = []
        self._frames = list(frames)
        self._index = 0
        self.closed = False

    def send(self, text):
        self.sent.append(text)

    def recv(self):
        if self._index >= len(self._frames):
            raise ws_lib.WebSocketConnectionClosedException()
        frame = self._frames[self._index]
        self._index += 1
        return frame

    def close(self):
        self.closed = True


def _patch_with_fake(monkeypatch, frames):
    fake = FakeWS(frames)
    monkeypatch.setattr("comwatt_client._streaming._open_websocket", lambda c, t: fake)
    return fake


def test_encode_frame_connect():
    frame = _encode_frame(
        "CONNECT", {"accept-version": "1.1,1.2", "heart-beat": "10000,10000"}
    )
    assert frame == "CONNECT\naccept-version:1.1,1.2\nheart-beat:10000,10000\n\n\x00"


def test_parse_frame_message():
    frame = 'MESSAGE\nmessage-id:msg-1\ndestination:/topic/x\n\n{"id":1}\x00'
    command, headers, body = _parse_frame(frame)
    assert command == "MESSAGE"
    assert headers == {"message-id": "msg-1", "destination": "/topic/x"}
    assert body == '{"id":1}'


def test_stream_measurements_yields_measurement_then_capacity_changed(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    _patch_with_fake(monkeypatch, [CONNECTED_FRAME, MEASURES_FRAME, PING_FRAME, CAPACITY_FRAME])

    events = list(client.stream_measurements(SITE))

    assert len(events) == 2
    m = events[0]
    assert isinstance(m, Measurement)
    assert m.gateway_uid == "BX"
    assert m.capacity_id == "co.1.sensor.0.data"
    assert m.measure_kind == "FLOW"
    assert m.value == "307.0"
    assert m.value_float == 307.0
    assert m.value_bool is None
    c = events[1]
    assert isinstance(c, CapacityChanged)
    assert c.capacity_id == 48067
    assert c.enable is True
    assert c.raw == {"id": 48067, "enable": True}


def test_stream_measurements_subscribes_siteuid_topic_and_starts_with_numeric_id(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    fake = _patch_with_fake(monkeypatch, [CONNECTED_FRAME, MEASURES_FRAME, PING_FRAME, CAPACITY_FRAME])

    list(client.stream_measurements(SITE))

    subscribe_frame = next(f for f in fake.sent if f.startswith("SUBSCRIBE\n"))
    send_frame = next(f for f in fake.sent if f.startswith("SEND\n"))
    _, sub_headers, _ = _parse_frame(subscribe_frame)
    assert sub_headers["destination"] == "/topic/sites/BX/capacityChanged"
    _, _, send_body = _parse_frame(send_frame)
    assert json.loads(send_body) == {"siteId": 12345}


def test_stream_measurements_passes_cookie_to_open_websocket(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    recorded = {}

    def fake_open(cookie, timeout):
        recorded["cookie"] = cookie
        recorded["timeout"] = timeout
        return FakeWS([CONNECTED_FRAME])

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", fake_open)

    list(client.stream_measurements(SITE))

    assert recorded["cookie"] == "abc123"


def test_stream_measurements_no_cookie_raises_auth_error(client):
    with pytest.raises(ComwattAuthError):
        list(client.stream_measurements(SITE))


def test_stream_measurements_missing_siteuid_raises_value_error(client):
    with pytest.raises(ValueError):
        list(client.stream_measurements({"id": 12345}))


def test_stream_measurements_missing_id_raises_value_error(client):
    with pytest.raises(ValueError):
        list(client.stream_measurements({"siteUid": "BX"}))


def test_stream_measurements_cleanup_on_exhaustion(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    fake = _patch_with_fake(monkeypatch, [CONNECTED_FRAME, MEASURES_FRAME])

    list(client.stream_measurements(SITE))

    assert fake.closed is True
    assert any(f.startswith("DISCONNECT") for f in fake.sent)


def test_stream_measurements_cleanup_on_early_close(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    fake = _patch_with_fake(monkeypatch, [CONNECTED_FRAME, MEASURES_FRAME, MEASURES_FRAME])

    gen = client.stream_measurements(SITE)
    next(gen)
    gen.close()

    assert fake.closed is True
    assert any(f.startswith("DISCONNECT") for f in fake.sent)


def test_stream_measurements_handshake_failure_raises_streaming_error(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    error_frame = _encode_frame("ERROR", {"message": "Bad CONNECT"})
    _patch_with_fake(monkeypatch, [error_frame])

    with pytest.raises(ComwattStreamingError):
        list(client.stream_measurements(SITE))


def test_open_websocket_url_and_cookie_header(monkeypatch):
    recorded = {}

    class DummyWS:
        pass

    def fake_cc(url, **kwargs):
        recorded["url"] = url
        recorded["kwargs"] = kwargs
        return DummyWS()

    monkeypatch.setattr(ws_lib, "create_connection", fake_cc)
    _open_websocket("abc123", 30)

    assert recorded["url"] == _WS_URL
    assert recorded["kwargs"]["header"] == ["Cookie: cwt_session=abc123"]


def test_stream_measurements_missing_extra_raises_streaming_error(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")

    def raise_import(cookie, timeout):
        raise ImportError("no websocket module")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", raise_import)

    with pytest.raises(ComwattStreamingError) as exc_info:
        list(client.stream_measurements(SITE))
    assert "comwatt-client[stream]" in str(exc_info.value)
