from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_electricity_price_success(client):
    mock_price = {
        "tempoSyntheses": {"blue": 300, "white": 43, "red": 22},
        "daily": [{"date": "2024-01-01", "color": "BLUE"}],
        "tempoSynthesesComplete": True,
    }
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricityprice",
        json=mock_price,
        status=200,
    )

    result = client.get_electricity_price(site_id="site-1")

    assert result == mock_price
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/electricityprice"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]


@responses.activate
def test_get_electricity_price_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/electricityprice",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_electricity_price(site_id="site-1")

    assert "500" in str(exc_info.value)
