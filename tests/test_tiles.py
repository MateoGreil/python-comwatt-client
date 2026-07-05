from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_tiles_success(client):
    mock_tiles = [
        {"id": 1, "type": "REAL_TIME", "deviceId": 10},
        {"id": 2, "type": "VALUATION", "deviceId": 20},
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/tiles",
        json=mock_tiles,
        status=200,
    )

    result = client.get_tiles(site_id="site-1")

    assert result == mock_tiles
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/tiles"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]


@responses.activate
def test_get_tiles_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/tiles",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_tiles(site_id="site-1")

    assert "500" in str(exc_info.value)
