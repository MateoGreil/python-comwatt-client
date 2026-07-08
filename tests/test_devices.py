import json
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_devices_success(client):
    mock_devices = [{"id": 1, "name": "Device One"}, {"id": 2, "name": "Device Two"}]
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices",
        json=mock_devices,
        status=200,
    )

    result = client.get_devices("site-1")

    assert result == mock_devices
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/devices"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]


@responses.activate
def test_get_devices_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_devices("site-1")

    assert "500" in str(exc_info.value)


@responses.activate
def test_get_device_success(client):
    mock_device = {"id": "device-1", "name": "Device One"}
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices/device-1",
        json=mock_device,
        status=200,
    )

    result = client.get_device("device-1")

    assert result == mock_device
    request = responses.calls[0].request
    assert request.method == "GET"
    assert request.url == f"{BASE_URL}/devices/device-1"


@responses.activate
def test_get_device_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices/device-1",
        json={},
        status=404,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_device("device-1")

    assert "device-1" in str(exc_info.value)
    assert "404" in str(exc_info.value)


@responses.activate
def test_put_device_success(client):
    mock_response = {"id": "device-1", "name": "Updated Device"}
    payload = {"name": "Updated Device"}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/devices/device-1",
        json=mock_response,
        status=200,
    )

    result = client.put_device("device-1", payload)

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    assert request.url == f"{BASE_URL}/devices/device-1"
    assert json.loads(request.body) == payload


@responses.activate
def test_put_device_error(client):
    payload = {"name": "Updated Device"}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/devices/device-1",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.put_device("device-1", payload)

    assert "500" in str(exc_info.value)

