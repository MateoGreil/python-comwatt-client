from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_connected_objects_by_site_success(client):
    mock_objects = [{"id": 1, "name": "Object One"}, {"id": 2, "name": "Object Two"}]
    responses.add(
        responses.GET,
        f"{BASE_URL}/connectedobjects",
        json=mock_objects,
        status=200,
    )

    result = client.get_connected_objects(site_id="site-1")

    assert result == mock_objects
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/connectedobjects"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]
    assert "gatewayUid" not in qs


@responses.activate
def test_get_connected_objects_by_gateway_success(client):
    mock_objects = [{"id": 1, "name": "Object One"}]
    responses.add(
        responses.GET,
        f"{BASE_URL}/connectedobjects",
        json=mock_objects,
        status=200,
    )

    result = client.get_connected_objects(gateway_uid="GW-1")

    assert result == mock_objects
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/connectedobjects"
    qs = parse_qs(parsed.query)
    assert qs["gatewayUid"] == ["GW-1"]
    assert "siteId" not in qs


@responses.activate
def test_get_connected_objects_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/connectedobjects",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_connected_objects(site_id="site-1")

    assert "500" in str(exc_info.value)


def test_get_connected_objects_requires_a_filter(client):
    with pytest.raises(ValueError):
        client.get_connected_objects()


def test_get_connected_objects_rejects_both_filters(client):
    with pytest.raises(ValueError):
        client.get_connected_objects(site_id="site-1", gateway_uid="GW-1")


@responses.activate
def test_get_connected_object_success(client):
    mock_object = {"id": "co-1", "name": "Object One"}
    responses.add(
        responses.GET,
        f"{BASE_URL}/connectedobjects/co-1",
        json=mock_object,
        status=200,
    )

    result = client.get_connected_object("co-1")

    assert result == mock_object
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/connectedobjects/co-1"


@responses.activate
def test_get_connected_object_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/connectedobjects/co-1",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_connected_object("co-1")

    assert "500" in str(exc_info.value)
