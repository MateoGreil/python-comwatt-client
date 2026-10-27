from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_products(client):
    products = [
        {
            "id": 8,
            "name": "MONITOR_GEN_4",
            "brand": "COMWATT",
            "cardinality": 0,
            "features": [
                {"id": 5, "code": "PLANNING", "featureName": "PLANNING"},
            ],
        },
        {"id": 9, "name": "POWER_GEN_4", "brand": "COMWATT", "cardinality": 1},
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/products",
        json=products,
        status=200,
    )

    result = client.get_products()

    assert result == products
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/products"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_products_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/products",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_products()

    assert "500" in str(exc_info.value)


@responses.activate
def test_get_product(client):
    product = {
        "id": 8,
        "name": "MONITOR_GEN_4",
        "brand": "COMWATT",
        "cardinality": 0,
        "features": [
            {"id": 5, "code": "PLANNING", "featureName": "PLANNING"},
        ],
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/products/8",
        json=product,
        status=200,
    )

    result = client.get_product(8)

    assert result == product
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/products/8"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_product_accepts_str_id(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/products/8",
        json={"id": 8, "name": "MONITOR_GEN_4", "brand": "COMWATT"},
        status=200,
    )

    client.get_product("8")

    parsed = urlparse(responses.calls[0].request.url)
    assert parsed.path == "/api/products/8"


@responses.activate
def test_get_product_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/products/8",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_product(8)

    assert "500" in str(exc_info.value)


@responses.activate
def test_get_timezones(client):
    timezones = [
        {"timeZone": "Europe/Paris", "posix": "CET-1CEST,M3.5.0,M10.5.0/3"},
        {"timeZone": "Indian/Reunion", "posix": "<+04>-4"},
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/util/timezones",
        json=timezones,
        status=200,
    )

    result = client.get_timezones()

    assert result == timezones
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/util/timezones"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_timezones_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/util/timezones",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_timezones()

    assert "500" in str(exc_info.value)


@responses.activate
def test_get_modbus_configurations(client):
    configurations = [
        {
            "id": 1,
            "name": "huawei",
            "label": "Huaweï Sun2000 nKTL",
            "port": 502,
            "slave": 1,
            "device_kinds": ["SOLAR_PANEL", "BATTERY", "GRID_METER"],
        },
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/modbus-configurations",
        json=configurations,
        status=200,
    )

    result = client.get_modbus_configurations()

    assert result == configurations
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/gateways/modbus-configurations"
    assert parse_qs(parsed.query) == {}


@responses.activate
def test_get_modbus_configurations_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/gateways/modbus-configurations",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_modbus_configurations()

    assert "500" in str(exc_info.value)
