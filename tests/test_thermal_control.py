import json
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


@responses.activate
def test_set_thermal_control_success_with_both_fields(client):
    mock_thermal_control = {
        "id": 55,
        "mode": "HEAT",
        "setPoint": 21.5,
        "deviceId": 7,
    }
    responses.add(
        responses.PUT,
        f"{BASE_URL}/thermalcontrol/55",
        json=mock_thermal_control,
        status=200,
    )

    result = client.set_thermal_control(
        thermal_control_id=55, device_id=7, set_point=21.5, mode="HEAT"
    )

    assert result == mock_thermal_control
    request = responses.calls[0].request
    assert request.method == "PUT"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/thermalcontrol/55"
    body = json.loads(request.body)
    assert body["device"] == {"@class": "Device", "id": 7}
    assert body["setPoint"] == 21.5
    assert body["mode"] == "HEAT"


@responses.activate
def test_set_thermal_control_success_with_set_point_only(client):
    mock_thermal_control = {
        "id": 55,
        "setPoint": 20.0,
        "deviceId": 7,
    }
    responses.add(
        responses.PUT,
        f"{BASE_URL}/thermalcontrol/55",
        json=mock_thermal_control,
        status=200,
    )

    result = client.set_thermal_control(
        thermal_control_id=55, device_id=7, set_point=20.0
    )

    assert result == mock_thermal_control
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    assert parsed.path == "/api/thermalcontrol/55"
    body = json.loads(request.body)
    assert body["device"] == {"@class": "Device", "id": 7}
    assert body["setPoint"] == 20.0
    assert "mode" not in body


@responses.activate
def test_set_thermal_control_accepts_str_device_id_as_numeric(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/thermalcontrol/55",
        json={"id": 55, "deviceId": 7},
        status=200,
    )

    client.set_thermal_control(thermal_control_id=55, device_id="7")

    request = responses.calls[0].request
    body = json.loads(request.body)
    assert body["device"]["id"] == 7
    assert body == {"device": {"@class": "Device", "id": 7}}


@responses.activate
def test_set_thermal_control_server_error_maps_to_comwatt_api_error(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/thermalcontrol/55",
        json={"detail": "Internal server error"},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.set_thermal_control(
            thermal_control_id=55, device_id=7, set_point=21.5, mode="HEAT"
        )

    assert exc_info.value.status_code == 500
    assert "500" in str(exc_info.value)
    assert exc_info.value.detail == "Internal server error"
