from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_switch_capacity_success_enable_true(client):
    mock_response = {"id": "capacity-1", "enabled": True}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/switch",
        json=mock_response,
        status=200,
    )

    result = client.switch_capacity("capacity-1", True)

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/capacities/capacity-1/switch"
    qs = parse_qs(parsed.query)
    assert qs["enable"] == ["true"]


@responses.activate
def test_switch_capacity_success_enable_false(client):
    mock_response = {"id": "capacity-1", "enabled": False}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/switch",
        json=mock_response,
        status=200,
    )

    result = client.switch_capacity("capacity-1", False)

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/capacities/capacity-1/switch"
    qs = parse_qs(parsed.query)
    assert qs["enable"] == ["false"]


@responses.activate
def test_switch_capacity_error(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/switch",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.switch_capacity("capacity-1", True)

    assert "500" in str(exc_info.value)


@responses.activate
def test_set_pilot_wire_success(client):
    mock_response = {"id": "capacity-1", "nature": "PILOT_WIRE"}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/pilot-wire",
        json=mock_response,
        status=200,
    )

    result = client.set_pilot_wire("capacity-1", "COMFORT")

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/capacities/capacity-1/pilot-wire"
    qs = parse_qs(parsed.query)
    assert qs["state"] == ["COMFORT"]


@responses.activate
def test_set_pilot_wire_error(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/pilot-wire",
        json={},
        status=400,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.set_pilot_wire("capacity-1", "NOT_A_STATE")

    assert "400" in str(exc_info.value)


@responses.activate
def test_set_thermal_mode_success(client):
    mock_response = {"id": "capacity-1", "nature": "THERMOSTAT"}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/thermal-mode",
        json=mock_response,
        status=200,
    )

    result = client.set_thermal_mode("capacity-1", "ECO")

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/capacities/capacity-1/thermal-mode"
    qs = parse_qs(parsed.query)
    assert qs["state"] == ["ECO"]


@responses.activate
def test_set_thermal_mode_error(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/thermal-mode",
        json={},
        status=400,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.set_thermal_mode("capacity-1", "NOPE")

    assert "400" in str(exc_info.value)


@responses.activate
def test_set_thermostat_set_point_success(client):
    mock_response = {"id": "capacity-1", "nature": "THERMOSTAT"}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/thermostat-set-point",
        json=mock_response,
        status=200,
    )

    result = client.set_thermostat_set_point("capacity-1", 19.5)

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/capacities/capacity-1/thermostat-set-point"
    qs = parse_qs(parsed.query)
    assert qs["value"] == ["19.5"]


@responses.activate
def test_set_thermostat_set_point_accepts_int(client):
    mock_response = {"id": "capacity-1"}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/thermostat-set-point",
        json=mock_response,
        status=200,
    )

    client.set_thermostat_set_point("capacity-1", 20)

    parsed = urlparse(responses.calls[0].request.url)
    qs = parse_qs(parsed.query)
    assert qs["value"] == ["20"]


@responses.activate
def test_set_thermostat_set_point_error(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/capacities/capacity-1/thermostat-set-point",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.set_thermostat_set_point("capacity-1", 21)

    assert "500" in str(exc_info.value)
