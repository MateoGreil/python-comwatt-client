import json
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_alert_configs_success(client):
    mock_alert_config = {
        "period": "SLIDING_24_HOURS",
        "id": 42,
        "min": 100.0,
        "max": 500.0,
        "activated": True,
        "deviceId": 7,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/alertconfigs/v2",
        json=mock_alert_config,
        status=200,
    )

    result = client.get_alert_configs(device_id=7)

    assert result == mock_alert_config
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/alertconfigs/v2"
    qs = parse_qs(parsed.query)
    assert qs["deviceId"] == ["7"]


@responses.activate
def test_get_alert_configs_unconfigured_device_returns_skeleton(client):
    skeleton_alert_config = {
        "period": "SLIDING_24_HOURS",
        "id": None,
        "min": None,
        "max": None,
        "activated": False,
        "deviceId": None,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/alertconfigs/v2",
        json=skeleton_alert_config,
        status=200,
    )

    result = client.get_alert_configs(device_id=7)

    assert result == skeleton_alert_config


@responses.activate
def test_get_alert_configs_server_error_maps_to_comwatt_api_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/alertconfigs/v2",
        json={"detail": "Required parameter 'deviceId' is not present."},
        status=400,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_alert_configs(device_id=7)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Required parameter 'deviceId' is not present."


@responses.activate
def test_set_alert_config_success(client):
    mock_alert_config = {
        "period": "SLIDING_24_HOURS",
        "id": 42,
        "min": 100.0,
        "max": 500.0,
        "activated": True,
        "deviceId": 7,
    }
    mock_updated_config = {
        "period": "SLIDING_24_HOURS",
        "id": 42,
        "min": 150.0,
        "max": 600.0,
        "activated": True,
        "deviceId": 7,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/alertconfigs/v2",
        json=mock_alert_config,
        status=200,
    )
    responses.add(
        responses.PUT,
        f"{BASE_URL}/alertconfigs/v2/42",
        json=mock_updated_config,
        status=200,
    )

    result = client.set_alert_config(device_id=7, min=150.0, max=600.0)

    assert result == mock_updated_config
    assert len(responses.calls) == 2
    get_request = responses.calls[0].request
    put_request = responses.calls[1].request
    assert get_request.method == "GET"
    parsed = urlparse(get_request.url)
    assert parsed.path == "/api/alertconfigs/v2"
    qs = parse_qs(parsed.query)
    assert qs["deviceId"] == ["7"]
    assert put_request.method == "PUT"
    assert urlparse(put_request.url).path == "/api/alertconfigs/v2/42"
    assert json.loads(put_request.body) == {
        "deviceId": 7,
        "min": 150.0,
        "max": 600.0,
        "period": "SLIDING_24_HOURS",
        "activated": True,
    }


@responses.activate
def test_set_alert_config_unconfigured_device_raises(client):
    skeleton_alert_config = {
        "period": "SLIDING_24_HOURS",
        "id": None,
        "min": None,
        "max": None,
        "activated": False,
        "deviceId": None,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/alertconfigs/v2",
        json=skeleton_alert_config,
        status=200,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.set_alert_config(device_id=7, min=150.0, max=600.0)

    assert "no alert config to update" in str(exc_info.value)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.method == "GET"


@responses.activate
def test_set_alert_config_put_server_error_maps_to_comwatt_api_error(client):
    mock_alert_config = {
        "period": "SLIDING_24_HOURS",
        "id": 42,
        "min": 100.0,
        "max": 500.0,
        "activated": True,
        "deviceId": 7,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/alertconfigs/v2",
        json=mock_alert_config,
        status=200,
    )
    responses.add(
        responses.PUT,
        f"{BASE_URL}/alertconfigs/v2/42",
        json={"detail": "Internal server error."},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.set_alert_config(device_id=7, min=150.0, max=600.0)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Internal server error."
    assert len(responses.calls) == 2
