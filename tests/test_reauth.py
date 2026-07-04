import pytest
import responses

from comwatt_client import ComwattAuthError, ComwattClient
from tests.conftest import BASE_URL


def _authenticate(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers={"Set-Cookie": "cwt_session=fake-session-token; Path=/"},
    )
    client.authenticate("testuser", "testpass")


@responses.activate
def test_get_sites_reauthenticates_on_401_and_retries(client):
    _authenticate(client)

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
        headers={"Set-Cookie": "cwt_session=fresh-session-token; Path=/"},
    )
    mock_sites = [{"id": 1, "name": "Site One"}]
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json=mock_sites,
        status=200,
    )

    result = client.get_sites()

    assert result == mock_sites
    authent_calls = [c for c in responses.calls if c.request.url == f"{BASE_URL}/v1/authent"]
    assert len(authent_calls) == 2


@responses.activate
def test_auto_reauth_false_raises_and_does_not_relogin(client_no_reauth):
    client = client_no_reauth
    _authenticate(client)

    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json={},
        status=401,
    )

    with pytest.raises(ComwattAuthError):
        client.get_sites()

    authent_calls = [c for c in responses.calls if c.request.url == f"{BASE_URL}/v1/authent"]
    assert len(authent_calls) == 1


@responses.activate
def test_no_stored_credentials_raises_without_reauth_attempt(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json={},
        status=401,
    )

    with pytest.raises(ComwattAuthError):
        client.get_sites()

    authent_calls = [c for c in responses.calls if c.request.url == f"{BASE_URL}/v1/authent"]
    assert len(authent_calls) == 0


@responses.activate
def test_reauth_then_still_401_raises_after_single_retry(client):
    _authenticate(client)

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
        headers={"Set-Cookie": "cwt_session=fresh-session-token; Path=/"},
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json={},
        status=401,
    )

    with pytest.raises(ComwattAuthError):
        client.get_sites()

    authent_calls = [c for c in responses.calls if c.request.url == f"{BASE_URL}/v1/authent"]
    assert len(authent_calls) == 2
    sites_calls = [c for c in responses.calls if c.request.url == f"{BASE_URL}/sites"]
    assert len(sites_calls) == 2


@responses.activate
def test_is_authenticated_not_affected_by_reauth(client):
    _authenticate(client)

    responses.add(
        responses.GET,
        f"{BASE_URL}/users/authenticated",
        json={},
        status=401,
    )

    result = client.is_authenticated()

    assert result is False
    authent_calls = [c for c in responses.calls if c.request.url == f"{BASE_URL}/v1/authent"]
    assert len(authent_calls) == 1


@responses.activate
def test_authenticate_retains_hash_only_not_raw_password(client):
    _authenticate_with_password(client, "s3cret")

    assert client._auth_hash == ComwattClient._hash_password("s3cret")
    assert "s3cret" not in vars(client).values()


def _authenticate_with_password(client, password):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
        headers={"Set-Cookie": "cwt_session=fake-session-token; Path=/"},
    )
    client.authenticate("testuser", password)
