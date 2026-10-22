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
