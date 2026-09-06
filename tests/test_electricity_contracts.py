from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_electricity_contract_empty(client):
    # A site with no contract returns an empty JSON array (verified live
    # 2026-09-06 on the probe account's contract-less site).
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricitycontract/3349",
        json=[],
        status=200,
    )

    result = client.get_electricity_contract(3349)

    assert result == []
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/electricitycontract/3349"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_electricity_contract_populated(client):
    contract = {
        "id": 7,
        "provider": "EDF",
        "contractType": "TEMPO",
        "startDate": "2026-01-01",
        "endDate": None,
        "siteId": 3349,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricitycontract/3349",
        json=[contract],
        status=200,
    )

    result = client.get_electricity_contract(3349)

    assert result == [contract]
    parsed = urlparse(responses.calls[0].request.url)
    assert parsed.path == "/api/electricitycontract/3349"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_electricity_contract_accepts_str_id(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricitycontract/3349",
        json=[],
        status=200,
    )

    client.get_electricity_contract("3349")

    parsed = urlparse(responses.calls[0].request.url)
    assert parsed.path == "/api/electricitycontract/3349"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_electricity_contract_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricitycontract/3349",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_electricity_contract(3349)

    assert "500" in str(exc_info.value)


@responses.activate
def test_get_electricity_contract_providers(client):
    providers = ["EDF", "TotalEnergies", "Octopus", "Mint", "Ekwateur"]
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricitycontract/providers",
        json=providers,
        status=200,
    )

    result = client.get_electricity_contract_providers()

    assert result == providers
    parsed = urlparse(responses.calls[0].request.url)
    assert parsed.path == "/api/electricitycontract/providers"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_electricity_contract_providers_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricitycontract/providers",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_electricity_contract_providers()

    assert "500" in str(exc_info.value)
