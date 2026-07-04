import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_authenticated_user_success(client):
    mock_user = {"id": 42, "username": "testuser", "email": "testuser@example.com"}
    responses.add(
        responses.GET,
        f"{BASE_URL}/users/authenticated",
        json=mock_user,
        status=200,
    )

    result = client.get_authenticated_user()

    assert result == mock_user
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.method == "GET"
    assert request.url == f"{BASE_URL}/users/authenticated"


@responses.activate
def test_get_authenticated_user_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/users/authenticated",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_authenticated_user()

    assert "500" in str(exc_info.value)


@responses.activate
def test_get_sites_success(client):
    mock_sites = [{"id": 1, "name": "Site One"}, {"id": 2, "name": "Site Two"}]
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json=mock_sites,
        status=200,
    )

    result = client.get_sites()

    assert result == mock_sites
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.method == "GET"
    assert request.url == f"{BASE_URL}/sites"


@responses.activate
def test_get_sites_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json={},
        status=404,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_sites()

    assert "404" in str(exc_info.value)
