import json

import pytest
import responses

from comwatt_client import ComwattAPIError, ComwattAuthError
from tests.conftest import BASE_URL


@responses.activate
def test_authenticate_success(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers={"Set-Cookie": "cwt_session=fake-session-token; Path=/"},
    )

    result = client.authenticate("testuser", "testpass")

    assert result is None
    assert client.session.cookies["cwt_session"] == "fake-session-token"
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.method == "POST"
    assert request.url == f"{BASE_URL}/v1/authent"
    body = json.loads(request.body)
    assert body["username"] == "testuser"
    assert (
        body["password"]
        == "d5a29cd5189cb9409b478fd31350c43aba0db9a8d3116da1331a2cd1424a4579"
    )


@responses.activate
def test_authenticate_missing_cookie(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.authenticate("testuser", "testpass")

    assert "cwt_session" in str(exc_info.value)


@responses.activate
def test_authenticate_error(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=401,
    )

    with pytest.raises(ComwattAuthError) as exc_info:
        client.authenticate("testuser", "testpass")

    assert "401" in str(exc_info.value)


@responses.activate
def test_authenticate_error_403(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=403,
    )

    with pytest.raises(ComwattAuthError) as exc_info:
        client.authenticate("testuser", "testpass")

    assert exc_info.value.status_code == 403


@responses.activate
def test_authenticate_server_error_is_not_auth_error(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=503,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.authenticate("testuser", "testpass")

    assert exc_info.value.status_code == 503


@responses.activate
def test_is_authenticated_true(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/users/authenticated",
        json={},
        status=200,
    )

    result = client.is_authenticated()

    assert result is True
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.method == "GET"
    assert request.url == f"{BASE_URL}/users/authenticated"


@responses.activate
def test_is_authenticated_false_on_401(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/users/authenticated",
        json={},
        status=401,
    )

    assert client.is_authenticated() is False


@responses.activate
def test_is_authenticated_false_on_403(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/users/authenticated",
        json={},
        status=403,
    )

    assert client.is_authenticated() is False


@responses.activate
def test_is_authenticated_raises_on_other_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/users/authenticated",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError):
        client.is_authenticated()


def _add_authent():
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers={"Set-Cookie": "cwt_session=fake-session-token; Path=/"},
    )


@responses.activate
def test_logout_success(client):
    _add_authent()
    responses.add(responses.POST, f"{BASE_URL}/v1/logout", status=200)
    client.authenticate("testuser", "testpass")

    result = client.logout()

    assert result is None
    logout_call = responses.calls[-1].request
    assert logout_call.method == "POST"
    assert logout_call.url == f"{BASE_URL}/v1/logout"
    assert client._username is None
    assert client._auth_hash is None


@responses.activate
def test_logout_idempotent_when_already_logged_out(client):
    responses.add(responses.POST, f"{BASE_URL}/v1/logout", status=401)

    result = client.logout()

    assert result is None
    assert client._username is None
    assert client._auth_hash is None


@responses.activate
def test_logout_prevents_auto_reauth(client):
    _add_authent()
    responses.add(responses.POST, f"{BASE_URL}/v1/logout", status=200)
    responses.add(responses.GET, f"{BASE_URL}/sites", json={}, status=401)
    client.authenticate("testuser", "testpass")

    client.logout()

    with pytest.raises(ComwattAuthError):
        client.get_sites()

    authent_calls = [
        call for call in responses.calls
        if call.request.url == f"{BASE_URL}/v1/authent"
    ]
    assert len(authent_calls) == 1


@responses.activate
def test_logout_keeps_credentials_on_unexpected_error(client):
    _add_authent()
    responses.add(responses.POST, f"{BASE_URL}/v1/logout", status=500)
    client.authenticate("testuser", "testpass")

    with pytest.raises(ComwattAPIError):
        client.logout()

    assert client._username == "testuser"
    assert client._auth_hash is not None
