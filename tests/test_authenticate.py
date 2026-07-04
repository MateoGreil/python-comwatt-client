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

    with pytest.raises(ComwattAuthError) as exc_info:
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
