from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_thermal_control_success(client):
    mock_thermal_control = {
        "mode": "AUTO",
        "setpoint": 21.0,
        "deviceId": 7,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/thermalcontrol",
        json=mock_thermal_control,
        status=200,
    )

    result = client.get_thermal_control(device_id=7)

    assert result == mock_thermal_control
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/thermalcontrol"
    qs = parse_qs(parsed.query)
    assert qs["deviceId"] == ["7"]


@responses.activate
def test_get_thermal_control_empty_body_returns_none(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/thermalcontrol",
        body="",
        status=200,
    )

    result = client.get_thermal_control(device_id=7)

    assert result is None


@responses.activate
def test_get_thermal_control_server_error_maps_to_comwatt_api_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/thermalcontrol",
        json={"detail": "Internal server error"},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_thermal_control(device_id=7)

    assert exc_info.value.status_code == 500
    assert "500" in str(exc_info.value)
    assert exc_info.value.detail == "Internal server error"
