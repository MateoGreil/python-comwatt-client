from urllib.parse import urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL

GATEWAY_ID = 359
GATEWAY_UID = "BXCCBB77D9"

GATEWAY_DOC = {
    "id": GATEWAY_ID,
    "gatewayUid": GATEWAY_UID,
    "connected": True,
    "updating": False,
    "status": "OK",
    "name": "Box salon",
    "product": {"kind": "POWER_GEN_4"},
    "networkConfiguration": {"ssid": "HomeWifi"},
}

NETWORK_DOC = dict(GATEWAY_DOC, networkConfiguration={
    "ssid": "HomeWifi",
    "signalStrength": -52,
    "channel": 6,
})

SSIDS = [
    {"ssid": "HomeWifi", "signalStrength": -52, "security": "WPA2"},
    {"ssid": "Voisin_2C7A", "signalStrength": -78, "security": "WPA2"},
]


@responses.activate
def test_get_gateway_success(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/{GATEWAY_ID}",
        json=GATEWAY_DOC,
        status=200,
    )

    result = client.get_gateway(gateway_id=GATEWAY_ID)

    assert result == GATEWAY_DOC
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/gateways/359"


@responses.activate
def test_get_gateway_by_uid_success(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/by-gateway-uid/{GATEWAY_UID}",
        json=GATEWAY_DOC,
        status=200,
    )

    result = client.get_gateway_by_uid(gateway_uid=GATEWAY_UID)

    assert result == GATEWAY_DOC
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == f"/api/gateways/by-gateway-uid/{GATEWAY_UID}"


@responses.activate
def test_get_gateway_network_success_uses_gateway_uid(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/{GATEWAY_UID}/network",
        json=NETWORK_DOC,
        status=200,
    )

    result = client.get_gateway_network(gateway_uid=GATEWAY_UID)

    assert result == NETWORK_DOC
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == f"/api/gateways/{GATEWAY_UID}/network"


@responses.activate
def test_get_gateway_network_wrong_id_maps_to_comwatt_api_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/{GATEWAY_ID}/network",
        json=[{"code": "gateway.not.found.for.fetching.network.details"}],
        status=412,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_gateway_network(gateway_uid=GATEWAY_ID)

    assert exc_info.value.status_code == 412


@responses.activate
def test_get_gateway_ssids_success(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/{GATEWAY_ID}/ssids",
        json=SSIDS,
        status=200,
    )

    result = client.get_gateway_ssids(gateway_id=GATEWAY_ID)

    assert result == SSIDS
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/gateways/359/ssids"


@responses.activate
def test_get_gateway_server_error_maps_to_comwatt_api_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/{GATEWAY_UID}",
        json={"detail": "Failed to convert 'gatewayId'"},
        status=400,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_gateway(gateway_id=GATEWAY_UID)

    assert exc_info.value.status_code == 400
