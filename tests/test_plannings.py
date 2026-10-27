import json
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_plannings_success_single_page(client):
    mock_plannings = [
        {"id": 1, "isDefault": True, "status": "OK"},
        {"id": 2, "isDefault": False, "status": "OK"},
    ]
    responses.add(
        responses.GET,
        f"{BASE_URL}/plannings",
        json={"content": mock_plannings, "totalPages": 1, "paginationSize": 20},
        status=200,
    )

    result = client.get_plannings(site_id="site-1")

    assert result == mock_plannings
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/plannings"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]
    assert qs["page"] == ["0"]


@responses.activate
def test_get_plannings_follows_all_pages(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/plannings",
        json={"content": [{"id": 1}], "totalPages": 2, "paginationSize": 1},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/plannings",
        json={"content": [{"id": 2}], "totalPages": 2, "paginationSize": 1},
        status=200,
    )

    result = client.get_plannings(site_id="site-1")

    assert result == [{"id": 1}, {"id": 2}]
    assert len(responses.calls) == 2
    qs_first = parse_qs(urlparse(responses.calls[0].request.url).query)
    qs_last = parse_qs(urlparse(responses.calls[1].request.url).query)
    assert qs_first["page"] == ["0"]
    assert qs_last["page"] == ["1"]


@responses.activate
def test_get_plannings_stops_on_empty_page_without_total_pages(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/plannings",
        json={"content": [{"id": 1}]},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/plannings",
        json={"content": []},
        status=200,
    )

    result = client.get_plannings(site_id="site-1")

    assert result == [{"id": 1}]
    assert len(responses.calls) == 2


@responses.activate
def test_get_plannings_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/plannings",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_plannings(site_id="site-1")

    assert "500" in str(exc_info.value)


@responses.activate
def test_update_planning_success(client):
    mock_response = {"id": 42, "name": "Winter planning"}
    payload = {
        "id": 42,
        "device": {"@class": "Device", "id": 7},
        "typicalDaySchedules": [
            {
                "typicalDay": {"id": 3, "startTime": "00:00:00", "endTime": "06:00:00"},
                "startTime": "07:00:00",
                "endTime": "09:00:00",
            }
        ],
    }
    responses.add(
        responses.PUT,
        f"{BASE_URL}/plannings/42",
        json=mock_response,
        status=200,
    )

    result = client.update_planning(planning_id=42, payload=payload)

    assert result == mock_response
    request = responses.calls[0].request
    assert request.method == "PUT"
    assert request.url == f"{BASE_URL}/plannings/42"
    assert json.loads(request.body) == payload


@responses.activate
def test_update_planning_error(client):
    responses.add(
        responses.PUT,
        f"{BASE_URL}/plannings/42",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.update_planning(planning_id=42, payload={"id": 42})

    assert "500" in str(exc_info.value)
