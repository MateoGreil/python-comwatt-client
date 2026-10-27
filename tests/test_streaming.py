import json
from datetime import datetime, timedelta, timezone

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
        if isinstance(frame, Exception):
            raise frame
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


# ---------------------------------------------------------------------------
# Helpers for reconnect tests
# ---------------------------------------------------------------------------

class FakeTime:
    def __init__(self, start=0.0):
        self.now = start
        self.sleep_args = []

    def sleep(self, s):
        self.sleep_args.append(s)
        self.now += s

    def monotonic(self):
        return self.now


class FakeRandom:
    def uniform(self, a, b):
        return b


# ---------------------------------------------------------------------------
# Reconnect tests (Task 1)
# ---------------------------------------------------------------------------


def test_stream_default_no_reconnect_single_open_call(monkeypatch, client):
    """Default (reconnect omitted): exactly one _open_websocket call; backward compat."""
    client.session.cookies.set("cwt_session", "abc123")
    open_calls = [0]
    fake = FakeWS([CONNECTED_FRAME, MEASURES_FRAME])

    def counting_open(cookie, timeout):
        open_calls[0] += 1
        return fake

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", counting_open)

    events = list(client.stream_measurements(SITE))

    assert open_calls[0] == 1
    assert len(events) == 1
    assert isinstance(events[0], Measurement)


def test_stream_reconnect_resumes_transparently(monkeypatch, client):
    """reconnect=True: measurements from two sessions are yielded in order."""
    client.session.cookies.set("cwt_session", "abc123")
    fake1 = FakeWS([CONNECTED_FRAME, MEASURES_FRAME])
    fake2 = FakeWS([CONNECTED_FRAME, MEASURES_FRAME])
    ws_iter = iter([fake1, fake2])
    open_calls = [0]

    def sequenced_open(cookie, timeout):
        open_calls[0] += 1
        try:
            return next(ws_iter)
        except StopIteration:
            raise ws_lib.WebSocketException("no more connections")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", sequenced_open)
    fake_time = FakeTime()
    monkeypatch.setattr("comwatt_client._streaming.time", fake_time)
    monkeypatch.setattr("comwatt_client._streaming.random", FakeRandom())

    events = []
    with pytest.raises(ComwattStreamingError):
        for e in client.stream_measurements(SITE, reconnect=True, reconnect_max_attempts=1):
            events.append(e)

    assert len(events) == 2
    assert all(isinstance(e, Measurement) for e in events)
    assert open_calls[0] == 3  # fake1, fake2, then one failed attempt → give up
    assert fake_time.sleep_args == []


def test_stream_exponential_backoff_with_cap(monkeypatch, client):
    """Backoff sequence: base, base*2, base*4, ..., capped at reconnect_backoff_max."""
    client.session.cookies.set("cwt_session", "abc123")

    def always_fail(cookie, timeout):
        raise ws_lib.WebSocketException("connection refused")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", always_fail)
    fake_time = FakeTime()
    monkeypatch.setattr("comwatt_client._streaming.time", fake_time)
    monkeypatch.setattr("comwatt_client._streaming.random", FakeRandom())

    with pytest.raises(ComwattStreamingError):
        list(client.stream_measurements(
            SITE, reconnect=True,
            reconnect_backoff=1.0,
            reconnect_backoff_max=4.0,
            reconnect_max_attempts=5,
        ))

    assert fake_time.sleep_args == [1.0, 2.0, 4.0, 4.0]


def test_stream_reconnect_gives_up_after_max_attempts(monkeypatch, client):
    """reconnect=True, always fails → ComwattStreamingError after reconnect_max_attempts."""
    client.session.cookies.set("cwt_session", "abc123")
    open_calls = [0]

    def always_fail(cookie, timeout):
        open_calls[0] += 1
        raise ws_lib.WebSocketException("connection refused")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", always_fail)
    monkeypatch.setattr("comwatt_client._streaming.time", FakeTime())
    monkeypatch.setattr("comwatt_client._streaming.random", FakeRandom())

    with pytest.raises(ComwattStreamingError) as exc_info:
        list(client.stream_measurements(SITE, reconnect=True, reconnect_max_attempts=3))

    assert open_calls[0] == 3
    assert "3" in str(exc_info.value)


def test_stream_connection_error_wrapping_no_reconnect(monkeypatch, client):
    """reconnect=False: WebSocketException from _open_websocket → ComwattStreamingError."""
    client.session.cookies.set("cwt_session", "abc123")

    def fail_open(cookie, timeout):
        raise ws_lib.WebSocketException("TLS error")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", fail_open)

    with pytest.raises(ComwattStreamingError):
        list(client.stream_measurements(SITE))


def test_stream_auth_refresh_on_connect(monkeypatch, client):
    """401 on first open → _reauthenticate called → second open returns working FakeWS."""
    client.session.cookies.set("cwt_session", "abc123")
    client._username = "user@example.com"
    client._auth_hash = "deadbeef"
    reauth_calls = [0]

    def fake_reauth():
        reauth_calls[0] += 1
        client.session.cookies.set("cwt_session", "new_token")

    client._reauthenticate = fake_reauth
    open_calls = [0]
    working_fake = FakeWS([CONNECTED_FRAME, MEASURES_FRAME])

    def open_with_first_401(cookie, timeout):
        open_calls[0] += 1
        if open_calls[0] == 1:
            raise ws_lib.WebSocketBadStatusException("Handshake status 401", 401)
        return working_fake

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", open_with_first_401)

    events = list(client.stream_measurements(SITE))

    assert reauth_calls[0] == 1
    assert open_calls[0] == 2
    assert len(events) == 1
    assert isinstance(events[0], Measurement)


def test_stream_auth_rejection_terminal(monkeypatch, client):
    """Always 401 → ComwattAuthError; _open_websocket called at most twice."""
    client.session.cookies.set("cwt_session", "abc123")
    client._username = "user@example.com"
    client._auth_hash = "deadbeef"
    client._reauthenticate = lambda: client.session.cookies.set("cwt_session", "new_token")
    open_calls = [0]

    def always_401(cookie, timeout):
        open_calls[0] += 1
        raise ws_lib.WebSocketBadStatusException("Handshake status 401", 401)

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", always_401)

    with pytest.raises(ComwattAuthError):
        list(client.stream_measurements(SITE))

    assert open_calls[0] == 2


def test_stream_backoff_resets_after_good_session(monkeypatch, client):
    """After a successful session, delay resets to reconnect_backoff before next failure sleep."""
    client.session.cookies.set("cwt_session", "abc123")
    fake1 = FakeWS([CONNECTED_FRAME, MEASURES_FRAME])
    open_calls = [0]

    def mixed_open(cookie, timeout):
        open_calls[0] += 1
        if open_calls[0] == 2:
            return fake1
        raise ws_lib.WebSocketException("connection failed")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", mixed_open)
    fake_time = FakeTime()
    monkeypatch.setattr("comwatt_client._streaming.time", fake_time)
    monkeypatch.setattr("comwatt_client._streaming.random", FakeRandom())

    events = []
    with pytest.raises(ComwattStreamingError):
        for e in client.stream_measurements(
            SITE, reconnect=True,
            reconnect_backoff=1.0,
            reconnect_backoff_max=60.0,
            reconnect_max_attempts=2,
        ):
            events.append(e)

    # attempt 1: fail → sleep(1.0), delay→2.0
    # attempt 2: fake1 connects → A → drops → RESET delay→1.0 (was 2.0)
    # attempt 3: fail → sleep(1.0) ← RESET, not 2.0
    # attempt 4: fail → max reached → raise
    assert fake_time.sleep_args == [1.0, 1.0]
    assert len(events) == 1


def test_stream_cleanup_under_reconnect(monkeypatch, client):
    """reconnect=True, gen.close() → FakeWS.closed is True and DISCONNECT was sent."""
    client.session.cookies.set("cwt_session", "abc123")
    fake = FakeWS([CONNECTED_FRAME, MEASURES_FRAME, MEASURES_FRAME])

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", lambda c, t: fake)
    monkeypatch.setattr("comwatt_client._streaming.time", FakeTime())
    monkeypatch.setattr("comwatt_client._streaming.random", FakeRandom())

    gen = client.stream_measurements(SITE, reconnect=True)
    next(gen)
    gen.close()

    assert fake.closed is True
    assert any(f.startswith("DISCONNECT") for f in fake.sent)


def test_stream_handshake_websocket_exc_no_reconnect_raises_and_closes(monkeypatch, client):
    """reconnect=False: WebSocketException during STOMP handshake → ComwattStreamingError, ws closed."""
    client.session.cookies.set("cwt_session", "abc123")
    fake = FakeWS([ws_lib.WebSocketException("server dropped during handshake")])
    monkeypatch.setattr("comwatt_client._streaming._open_websocket", lambda c, t: fake)

    with pytest.raises(ComwattStreamingError, match="STOMP handshake"):
        list(client.stream_measurements(SITE))

    assert fake.closed is True


def test_stream_handshake_websocket_exc_retried_with_reconnect(monkeypatch, client):
    """reconnect=True: WebSocketException during handshake is caught and retried; second attempt delivers measurement."""
    client.session.cookies.set("cwt_session", "abc123")
    fake1 = FakeWS([ws_lib.WebSocketException("server dropped during handshake")])
    fake2 = FakeWS([CONNECTED_FRAME, MEASURES_FRAME])
    ws_queue = [fake1, fake2]

    def sequenced_open(cookie, timeout):
        if ws_queue:
            return ws_queue.pop(0)
        raise ws_lib.WebSocketException("no more connections")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", sequenced_open)
    monkeypatch.setattr("comwatt_client._streaming.time", FakeTime())
    monkeypatch.setattr("comwatt_client._streaming.random", FakeRandom())

    events = []
    with pytest.raises(ComwattStreamingError):
        for e in client.stream_measurements(SITE, reconnect=True, reconnect_max_attempts=2):
            events.append(e)

    assert len(events) == 1
    assert isinstance(events[0], Measurement)


def test_stream_reconnect_uses_fresh_cookie_after_reauth(monkeypatch, client):
    """After reauthentication in iteration 1, subsequent reconnect iterations use the new cookie."""
    client.session.cookies.set("cwt_session", "old_token")
    client._username = "user@example.com"
    client._auth_hash = "deadbeef"

    def fake_reauth():
        client.session.cookies.set("cwt_session", "new_token")

    client._reauthenticate = fake_reauth
    recorded_cookies = []
    call_count = [0]

    def recording_open(cookie, timeout):
        recorded_cookies.append(cookie)
        call_count[0] += 1
        if call_count[0] == 1:
            raise ws_lib.WebSocketBadStatusException("Handshake status 401", 401)
        if call_count[0] == 2:
            return FakeWS([CONNECTED_FRAME, MEASURES_FRAME])
        raise ws_lib.WebSocketException("end of test")

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", recording_open)
    monkeypatch.setattr("comwatt_client._streaming.time", FakeTime())
    monkeypatch.setattr("comwatt_client._streaming.random", FakeRandom())

    with pytest.raises(ComwattStreamingError):
        list(client.stream_measurements(SITE, reconnect=True, reconnect_max_attempts=1))

    assert recorded_cookies[0] == "old_token"
    assert recorded_cookies[1] == "new_token"
    assert recorded_cookies[2] == "new_token"


def _spy_reauth(client):
    reauth_calls = [0]

    def fake_reauth():
        reauth_calls[0] += 1
        client._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
        client.session.cookies.set("cwt_session", "new_token")

    client._reauthenticate = fake_reauth
    return reauth_calls


def test_stream_start_reauthenticates_proactively_when_expired(monkeypatch, client):
    """Expired session + auto_reauth + stored creds -> re-auth BEFORE the WS
    handshake, which then uses the fresh cookie (no 401 round trip)."""
    client.session.cookies.set("cwt_session", "abc123")
    client._username = "user@example.com"
    client._auth_hash = "deadbeef"
    client._session_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    reauth_calls = _spy_reauth(client)
    open_cookies = []

    def open_record(cookie, timeout):
        open_cookies.append(cookie)
        return FakeWS([CONNECTED_FRAME, MEASURES_FRAME])

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", open_record)

    events = list(client.stream_measurements(SITE))

    assert reauth_calls[0] == 1
    assert open_cookies == ["new_token"]
    assert len(events) == 1
    assert isinstance(events[0], Measurement)


def test_stream_start_no_proactive_reauth_when_expiry_far(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    client._username = "user@example.com"
    client._auth_hash = "deadbeef"
    client._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    reauth_calls = _spy_reauth(client)

    monkeypatch.setattr(
        "comwatt_client._streaming._open_websocket",
        lambda c, t: FakeWS([CONNECTED_FRAME, MEASURES_FRAME]),
    )

    list(client.stream_measurements(SITE))

    assert reauth_calls[0] == 0


def test_stream_reconnect_reauthenticates_proactively_when_expired_mid_stream(monkeypatch, client):
    """reconnect=True: session expires right after the first handshake -> the
    reconnect handshake re-auths proactively and uses the fresh cookie."""
    client.session.cookies.set("cwt_session", "abc123")
    client._username = "user@example.com"
    client._auth_hash = "deadbeef"
    client._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    reauth_calls = _spy_reauth(client)
    open_cookies = []
    open_calls = [0]

    def open_two_sessions(cookie, timeout):
        open_calls[0] += 1
        open_cookies.append(cookie)
        if open_calls[0] == 1:
            client._session_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        return FakeWS([CONNECTED_FRAME, MEASURES_FRAME])

    monkeypatch.setattr("comwatt_client._streaming._open_websocket", open_two_sessions)

    gen = client.stream_measurements(SITE, reconnect=True)
    events = [next(gen), next(gen)]
    gen.close()

    assert open_calls[0] == 2
    assert reauth_calls[0] == 1
    assert open_cookies == ["abc123", "new_token"]
    assert len(events) == 2


def test_stream_no_proactive_reauth_without_stored_credentials(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    client._session_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    reauth_calls = _spy_reauth(client)

    monkeypatch.setattr(
        "comwatt_client._streaming._open_websocket",
        lambda c, t: FakeWS([CONNECTED_FRAME, MEASURES_FRAME]),
    )

    events = list(client.stream_measurements(SITE))

    assert reauth_calls[0] == 0
    assert len(events) == 1


def test_stream_no_proactive_reauth_when_auto_reauth_false(monkeypatch, client_no_reauth):
    client = client_no_reauth
    client.session.cookies.set("cwt_session", "abc123")
    client._username = "user@example.com"
    client._auth_hash = "deadbeef"
    client._session_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    reauth_calls = _spy_reauth(client)

    monkeypatch.setattr(
        "comwatt_client._streaming._open_websocket",
        lambda c, t: FakeWS([CONNECTED_FRAME, MEASURES_FRAME]),
    )

    events = list(client.stream_measurements(SITE))

    assert reauth_calls[0] == 0
    assert len(events) == 1


# ---------------------------------------------------------------------------
# __ping__ keep-alive tests (issue #101)
# ---------------------------------------------------------------------------

class AdvancingTimeoutWS:
    """recv raises the websocket timeout (like a silent socket), advancing
    fake time by `advance` s per call; once `timeouts` is exhausted, raises
    connection-closed to end the stream."""

    def __init__(self, fake_time, advance, timeouts):
        self.sent = []
        self.closed = False
        self._fake_time = fake_time
        self._advance = advance
        self._timeouts = timeouts
        self._handshake_pending = True

    def send(self, text):
        self.sent.append(text)

    def recv(self):
        if self._handshake_pending:
            self._handshake_pending = False
            return CONNECTED_FRAME
        self._fake_time.now += self._advance
        if self._timeouts <= 0:
            raise ws_lib.WebSocketConnectionClosedException()
        self._timeouts -= 1
        raise ws_lib.WebSocketTimeoutException()

    def close(self):
        self.closed = True


def test_stream_pings_after_60s_of_silence(monkeypatch, client):
    """The server declines STOMP heart-beats (CONNECTED heart-beat:0,0), so
    the keep-alive is the raw text __ping__, every 60 s — mirroring the SPA.
    Socket timeouts (previously an unhandled crash) now just wake the loop."""
    client.session.cookies.set("cwt_session", "abc123")
    fake_time = FakeTime()
    monkeypatch.setattr("comwatt_client._streaming.time", fake_time)
    fake = AdvancingTimeoutWS(fake_time, advance=31, timeouts=2)
    monkeypatch.setattr("comwatt_client._streaming._open_websocket", lambda c, t: fake)

    list(client.stream_measurements(SITE))

    assert fake.sent.count("__ping__") == 1


def test_stream_no_ping_before_60s(monkeypatch, client):
    client.session.cookies.set("cwt_session", "abc123")
    fake_time = FakeTime()
    monkeypatch.setattr("comwatt_client._streaming.time", fake_time)
    fake = AdvancingTimeoutWS(fake_time, advance=20, timeouts=2)
    monkeypatch.setattr("comwatt_client._streaming._open_websocket", lambda c, t: fake)

    list(client.stream_measurements(SITE))

    assert "__ping__" not in fake.sent


def test_stream_pings_during_ongoing_traffic(monkeypatch, client):
    """Pings are time-based, independent of traffic: 60 s elapsed between two
    frames -> __ping__ goes out before the next recv."""
    client.session.cookies.set("cwt_session", "abc123")
    fake_time = FakeTime()
    monkeypatch.setattr("comwatt_client._streaming.time", fake_time)

    class TrafficWithTimeJumpWS(AdvancingTimeoutWS):
        def __init__(self):
            super().__init__(fake_time, advance=0, timeouts=0)
            self._calls = 0

        def recv(self):
            self._calls += 1
            if self._calls == 1:
                return CONNECTED_FRAME
            if self._calls == 2:
                self._fake_time.now += 61
                return MEASURES_FRAME
            raise ws_lib.WebSocketConnectionClosedException()

    fake = TrafficWithTimeJumpWS()
    monkeypatch.setattr("comwatt_client._streaming._open_websocket", lambda c, t: fake)

    events = list(client.stream_measurements(SITE))

    assert "__ping__" in fake.sent
    assert len(events) == 1
    assert isinstance(events[0], Measurement)


def test_stream_dead_socket_at_ping_time_ends_cleanly(monkeypatch, client):
    """If __ping__ itself fails on a dead socket, the stream ends instead of
    leaking a raw websocket-client exception."""
    client.session.cookies.set("cwt_session", "abc123")
    fake_time = FakeTime()
    monkeypatch.setattr("comwatt_client._streaming.time", fake_time)

    class DeadOnPingWS(AdvancingTimeoutWS):
        def send(self, text):
            if text == "__ping__":
                raise ws_lib.WebSocketConnectionClosedException()
            self.sent.append(text)

    fake = DeadOnPingWS(fake_time, advance=61, timeouts=1)
    monkeypatch.setattr("comwatt_client._streaming._open_websocket", lambda c, t: fake)

    list(client.stream_measurements(SITE))

    assert fake.sent.count("__ping__") == 0
    assert fake.closed is True
