import json
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


@responses.activate
def test_create_typical_day_success(client):
    mock_response = {
        "id": 42,
        "label": "Winter weekday",
        "isDefault": False,
        "timeRangeConfigurations": [],
    }
    payload = {
        "label": "Winter weekday",
        "isDefault": False,
        "timeRangeConfigurations": [
            {"startTime": "06:00", "endTime": "22:00", "mode": "COMWATT"}
        ],
    }
    responses.add(
        responses.POST,
        f"{BASE_URL}/typicaldays",
        json=mock_response,
        status=200,
    )

    result = client.create_typical_day(site_id="site-1", payload=payload)

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "POST"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/typicaldays"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]
    assert json.loads(request.body) == payload


@responses.activate
def test_create_typical_day_error(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/typicaldays",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.create_typical_day(site_id="site-1", payload={"label": "x"})

    assert "500" in str(exc_info.value)


@responses.activate
def test_update_typical_day_success(client):
    mock_response = {
        "id": 42,
        "label": "Renamed",
        "isDefault": False,
        "timeRangeConfigurations": [],
    }
    payload = {"label": "Renamed"}
    responses.add(
        responses.PUT,
        f"{BASE_URL}/typicaldays/42",
        json=mock_response,
        status=200,
    )

    result = client.update_typical_day(typical_day_id=42, payload=payload)

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    assert request.url == f"{BASE_URL}/typicaldays/42"
    assert json.loads(request.body) == payload


@responses.activate
def test_update_typical_day_error(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/typicaldays/42",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.update_typical_day(typical_day_id=42, payload={"label": "x"})

    assert "500" in str(exc_info.value)
