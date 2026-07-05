from urllib.parse import urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_device_kinds_success(client):
    mock_kinds = [{"id": 1, "code": "SOLAR_PANEL"}, {"id": 2, "code": "GRID_METER"}]
    responses.add(
        responses.GET,
        f"{BASE_URL}/devicekinds/by-site-uid/992179e1",
        json=mock_kinds,
        status=200,
    )

    result = client.get_device_kinds("992179e1")

    assert result == mock_kinds
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/devicekinds/by-site-uid/992179e1"


@responses.activate
def test_get_device_kinds_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/devicekinds/by-site-uid/992179e1",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_device_kinds("992179e1")

    assert "500" in str(exc_info.value)
