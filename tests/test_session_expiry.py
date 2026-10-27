from datetime import datetime, timedelta, timezone

import responses

from comwatt_client import ComwattClient
from tests.conftest import BASE_URL


def _authenticate(client, expires="2026-10-27T12:03:42.627Z"):
    headers = {"Set-Cookie": "cwt_session=fake-session-token; Path=/"}
    if expires is not None:
        headers["x-cwt-token"] = expires
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers=headers,
    )
    client.authenticate("testuser", "testpass")


def test_session_expires_at_is_none_before_authenticate():
    client = ComwattClient()

    assert client.session_expires_at is None


@responses.activate
def test_session_expires_at_parses_x_cwt_token_header(client):
    _authenticate(client)

    assert client.session_expires_at == datetime(
        2026, 10, 27, 12, 3, 42, 627000, tzinfo=timezone.utc
    )


@responses.activate
def test_session_expires_at_handles_offset_form(client):
    _authenticate(client, expires="2026-10-27T14:03:42.627+02:00")

    assert client.session_expires_at == datetime(
        2026, 10, 27, 14, 3, 42, 627000, tzinfo=timezone(timedelta(hours=2))
    )


@responses.activate
def test_session_expires_at_none_when_header_absent(client):
    _authenticate(client, expires=None)

    assert client.session_expires_at is None


@responses.activate
def test_session_expires_at_none_when_header_malformed(client):
    _authenticate(client, expires="not-a-date")

    assert client.session_expires_at is None


@responses.activate
def test_session_expires_at_refreshed_on_reactive_reauth(client):
    _authenticate(client, expires="2026-10-27T10:00:00Z")

    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json={},
        status=401,
    )
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers={
            "Set-Cookie": "cwt_session=fresh-session-token; Path=/",
            "x-cwt-token": "2026-10-27T14:00:00Z",
        },
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json=[{"id": 1}],
        status=200,
    )

    client.get_sites()

    assert client.session_expires_at == datetime(2026, 10, 27, 14, 0, 0, tzinfo=timezone.utc)


@responses.activate
def test_session_expires_at_cleared_on_logout(client):
    _authenticate(client)
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/logout",
        json={},
        status=200,
    )

    client.logout()

    assert client.session_expires_at is None
