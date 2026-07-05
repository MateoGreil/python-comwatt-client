from urllib.parse import urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_ecowatt_success(client):
    mock_ecowatt = [
        {
            "id": 1,
            "updatedAt": "2024-01-01T00:00:00Z",
            "retrievedAt": "2024-01-01T00:05:00Z",
            "date": "2024-01-01",
            "status": "GREEN",
            "hourly": [1] * 24,
        },
        {
            "id": 2,
            "updatedAt": "2024-01-02T00:00:00Z",
            "retrievedAt": "2024-01-02T00:05:00Z",
            "date": "2024-01-02",
            "status": "ORANGE",
            "hourly": [2] * 24,
        },
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/ecowatt",
        json=mock_ecowatt,
        status=200,
    )

    result = client.get_ecowatt()

    assert result == mock_ecowatt
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/ecowatt"


@responses.activate
def test_get_ecowatt_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/ecowatt",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_ecowatt()

    assert "500" in str(exc_info.value)
