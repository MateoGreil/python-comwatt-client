from datetime import datetime, timedelta, timezone

import responses

from comwatt_client import ComwattClient
from tests.conftest import BASE_URL


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def _authenticate(client, expires_at: datetime):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers={
            "Set-Cookie": "cwt_session=fake-session-token; Path=/",
            "x-cwt-token": _iso(expires_at),
        },
    )
    client.authenticate("testuser", "testpass")


def _add_fresh_authent():
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers={
            "Set-Cookie": "cwt_session=fresh-session-token; Path=/",
            "x-cwt-token": _iso(datetime.now(timezone.utc) + timedelta(hours=2)),
        },
    )


def _add_sites_ok():
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json=[{"id": 1}],
        status=200,
    )


def _authent_calls():
    return [c for c in responses.calls if c.request.url == f"{BASE_URL}/v1/authent"]


@responses.activate
def test_auto_reauth_reauthenticates_proactively_when_expired(client):
    _authenticate(client, datetime.now(timezone.utc) - timedelta(minutes=10))
    _add_fresh_authent()
    _add_sites_ok()

    result = client.get_sites()

    assert result == [{"id": 1}]
    assert len(_authent_calls()) == 2
    assert client.session_expires_at > datetime.now(timezone.utc) + timedelta(hours=1)


@responses.activate
def test_auto_reauth_reauthenticates_proactively_inside_margin(client):
    _authenticate(client, datetime.now(timezone.utc) + timedelta(seconds=10))
    _add_fresh_authent()
    _add_sites_ok()

    client.get_sites()

    assert len(_authent_calls()) == 2


@responses.activate
def test_auto_reauth_no_proactive_relogin_when_expiry_far(client):
    _authenticate(client, datetime.now(timezone.utc) + timedelta(hours=1))
    _add_sites_ok()

    client.get_sites()

    assert len(_authent_calls()) == 1


@responses.activate
def test_auto_reauth_false_disables_proactive_relogin(client_no_reauth):
    client = client_no_reauth
    _authenticate(client, datetime.now(timezone.utc) - timedelta(minutes=10))
    _add_sites_ok()

    client.get_sites()

    assert len(_authent_calls()) == 1


@responses.activate
def test_auto_reauth_proactive_noop_without_stored_credentials():
    client = ComwattClient()
    _add_sites_ok()

    client.get_sites()

    assert len(_authent_calls()) == 0
