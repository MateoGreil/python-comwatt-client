from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_typical_days_success_single_page(client):
    mock_typical_days = [
        {
            "id": 1,
            "label": "Weekday",
            "isDefault": True,
            "timeRangeConfigurations": [
                {"startTime": "06:00", "endTime": "22:00", "mode": "COMWATT"}
            ],
        },
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/typicaldays",
        json={"content": mock_typical_days, "totalPages": 1, "paginationSize": 20},
        status=200,
    )

    result = client.get_typical_days(site_id="site-1")

    assert result == mock_typical_days
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/typicaldays"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]
    assert qs["page"] == ["0"]


@responses.activate
def test_get_typical_days_follows_all_pages(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/typicaldays",
        json={"content": [{"id": 1}], "totalPages": 2, "paginationSize": 1},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/typicaldays",
        json={"content": [{"id": 2}], "totalPages": 2, "paginationSize": 1},
        status=200,
    )

    result = client.get_typical_days(site_id="site-1")

    assert result == [{"id": 1}, {"id": 2}]
    assert len(responses.calls) == 2
    qs_first = parse_qs(urlparse(responses.calls[0].request.url).query)
    qs_last = parse_qs(urlparse(responses.calls[1].request.url).query)
    assert qs_first["page"] == ["0"]
    assert qs_last["page"] == ["1"]


@responses.activate
def test_get_typical_days_stops_on_empty_page_without_total_pages(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/typicaldays",
        json={"content": [{"id": 1}]},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/typicaldays",
        json={"content": []},
        status=200,
    )

    result = client.get_typical_days(site_id="site-1")

    assert result == [{"id": 1}]
    assert len(responses.calls) == 2


@responses.activate
def test_get_typical_days_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/typicaldays",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_typical_days(site_id="site-1")

    assert "500" in str(exc_info.value)
