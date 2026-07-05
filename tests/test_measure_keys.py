from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_measure_keys_success(client):
    mock_measure_keys = [
        {"id": 1, "measureKind": "FLOW", "measureKey": "uuid-1"},
        {"id": 2, "measureKind": "QUANTITY", "measureKey": "uuid-2"},
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/measurekeys/measurekeys",
        json=mock_measure_keys,
        status=200,
    )

    result = client.get_measure_keys(site_id="site-1")

    assert result == mock_measure_keys
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/measurekeys/measurekeys"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]


@responses.activate
def test_get_measure_keys_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/measurekeys/measurekeys",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_measure_keys(site_id="site-1")

    assert "500" in str(exc_info.value)
