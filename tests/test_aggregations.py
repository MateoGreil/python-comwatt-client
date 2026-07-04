from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_get_site_networks_ts_time_ago_defaults(client):
    mock_data = {"values": [1, 2, 3]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_networks_ts_time_ago("site-1")

    assert result == mock_data
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/aggregations/site-networks-ts-time-ago"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]
    assert qs["measureKind"] == ["FLOW"]
    assert qs["aggregationLevel"] == ["NONE"]
    assert qs["timeAgoUnit"] == ["HOUR"]
    assert qs["timeAgoValue"] == ["1"]
    assert "aggregationType" not in qs


@responses.activate
def test_get_site_networks_ts_time_ago_with_aggregation_type(client):
    mock_data = {"values": [4, 5, 6]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_networks_ts_time_ago("site-1", aggregation_type="SUM")

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["aggregationType"] == ["SUM"]


@responses.activate
def test_get_site_networks_ts_time_ago_custom_params(client):
    mock_data = {"values": [7, 8, 9]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_networks_ts_time_ago(
        "site-1",
        measure_kind="VIRTUAL_QUANTITY",
        aggregation_level="DAY",
        time_ago_unit="MONTH",
        time_ago_value=3,
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["measureKind"] == ["VIRTUAL_QUANTITY"]
    assert qs["aggregationLevel"] == ["DAY"]
    assert qs["timeAgoUnit"] == ["MONTH"]
    assert qs["timeAgoValue"] == ["3"]


@responses.activate
def test_get_site_networks_ts_time_ago_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_site_networks_ts_time_ago("site-1")

    assert "500" in str(exc_info.value)


@responses.activate
def test_get_site_consumption_breakdown_time_ago_defaults(client):
    mock_data = {"breakdown": "data"}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/consumption-breakdown-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_consumption_breakdown_time_ago("site-1")

    assert result == mock_data
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/aggregations/consumption-breakdown-time-ago"
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]
    assert qs["aggregationLevel"] == ["HOUR"]
    assert qs["timeAgoUnit"] == ["DAY"]
    assert qs["timeAgoValue"] == ["1"]


@responses.activate
def test_get_site_consumption_breakdown_time_ago_custom_params(client):
    mock_data = {"breakdown": "custom"}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/consumption-breakdown-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_consumption_breakdown_time_ago(
        "site-1",
        aggregation_level="DAY",
        time_ago_unit="MONTH",
        time_ago_value=2,
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["siteId"] == ["site-1"]
    assert qs["aggregationLevel"] == ["DAY"]
    assert qs["timeAgoUnit"] == ["MONTH"]
    assert qs["timeAgoValue"] == ["2"]


@responses.activate
def test_get_site_consumption_breakdown_time_ago_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/consumption-breakdown-time-ago",
        json={},
        status=404,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_site_consumption_breakdown_time_ago("site-1")

    assert "404" in str(exc_info.value)


@responses.activate
def test_get_device_ts_time_ago_defaults(client):
    mock_data = {"series": [1, 2, 3]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json=mock_data,
        status=200,
    )

    result = client.get_device_ts_time_ago("device-1")

    assert result == mock_data
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/api/aggregations/time-series"
    qs = parse_qs(parsed.query)
    assert qs["id"] == ["device-1"]
    assert qs["measureKind"] == ["FLOW"]
    assert qs["aggregationLevel"] == ["HOUR"]
    assert qs["aggregationType"] == ["MAX"]
    assert qs["timeAgoUnit"] == ["DAY"]
    assert qs["timeAgoValue"] == ["1"]


@responses.activate
def test_get_site_networks_ts_time_ago_with_naive_start(client):
    mock_data = {"values": [1]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_networks_ts_time_ago(
        "site-1", start=datetime(2026, 7, 4, 10, 0, 0)
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T10:00:00Z"]
    assert "timeAgoUnit" not in qs
    assert "timeAgoValue" not in qs
    assert "end" not in qs
    assert qs["measureKind"] == ["FLOW"]
    assert qs["aggregationLevel"] == ["NONE"]


@responses.activate
def test_get_site_networks_ts_time_ago_with_start_and_end(client):
    mock_data = {"values": [2]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_networks_ts_time_ago(
        "site-1",
        start=datetime(2026, 7, 4, 0, 0, 0),
        end=datetime(2026, 7, 5, 0, 0, 0),
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T00:00:00Z"]
    assert qs["end"] == ["2026-07-05T00:00:00Z"]
    assert "timeAgoUnit" not in qs
    assert "timeAgoValue" not in qs


@responses.activate
def test_get_site_networks_ts_time_ago_with_aware_start(client):
    mock_data = {"values": [3]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json=mock_data,
        status=200,
    )

    aware = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    result = client.get_site_networks_ts_time_ago("site-1", start=aware)

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T10:00:00Z"]


@responses.activate
def test_get_site_networks_ts_time_ago_with_string_start(client):
    mock_data = {"values": [4]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/site-networks-ts-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_networks_ts_time_ago(
        "site-1", start="2026-07-04T10:00:00Z"
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T10:00:00Z"]


@responses.activate
def test_get_site_networks_ts_time_ago_end_without_start_raises(client):
    with pytest.raises(ValueError):
        client.get_site_networks_ts_time_ago(
            "site-1", end=datetime(2026, 7, 4, 10, 0, 0)
        )
    assert len(responses.calls) == 0


@responses.activate
def test_get_site_consumption_breakdown_time_ago_with_start_and_end(client):
    mock_data = {"breakdown": "windowed"}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/consumption-breakdown-time-ago",
        json=mock_data,
        status=200,
    )

    result = client.get_site_consumption_breakdown_time_ago(
        "site-1",
        start=datetime(2026, 7, 4, 0, 0, 0),
        end=datetime(2026, 7, 5, 0, 0, 0),
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T00:00:00Z"]
    assert qs["end"] == ["2026-07-05T00:00:00Z"]
    assert "timeAgoUnit" not in qs
    assert "timeAgoValue" not in qs


@responses.activate
def test_get_site_consumption_breakdown_time_ago_end_without_start_raises(client):
    with pytest.raises(ValueError):
        client.get_site_consumption_breakdown_time_ago(
            "site-1", end=datetime(2026, 7, 4, 10, 0, 0)
        )
    assert len(responses.calls) == 0


@responses.activate
def test_get_device_ts_time_ago_with_naive_start(client):
    mock_data = {"series": [1]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json=mock_data,
        status=200,
    )

    result = client.get_device_ts_time_ago(
        "device-1", start=datetime(2026, 7, 4, 10, 0, 0)
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T10:00:00Z"]
    assert "timeAgoUnit" not in qs
    assert "timeAgoValue" not in qs
    assert qs["measureKind"] == ["FLOW"]
    assert qs["aggregationType"] == ["MAX"]


@responses.activate
def test_get_device_ts_time_ago_with_start_and_end(client):
    mock_data = {"series": [2]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json=mock_data,
        status=200,
    )

    result = client.get_device_ts_time_ago(
        "device-1",
        start=datetime(2026, 7, 4, 0, 0, 0),
        end=datetime(2026, 7, 5, 0, 0, 0),
    )

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T00:00:00Z"]
    assert qs["end"] == ["2026-07-05T00:00:00Z"]


@responses.activate
def test_get_device_ts_time_ago_with_aware_start(client):
    mock_data = {"series": [3]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json=mock_data,
        status=200,
    )

    aware = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    result = client.get_device_ts_time_ago("device-1", start=aware)

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T10:00:00Z"]


@responses.activate
def test_get_device_ts_time_ago_with_string_start(client):
    mock_data = {"series": [4]}
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json=mock_data,
        status=200,
    )

    result = client.get_device_ts_time_ago("device-1", start="2026-07-04T10:00:00Z")

    assert result == mock_data
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["start"] == ["2026-07-04T10:00:00Z"]


@responses.activate
def test_get_device_ts_time_ago_end_without_start_raises(client):
    with pytest.raises(ValueError):
        client.get_device_ts_time_ago("device-1", end=datetime(2026, 7, 4, 10, 0, 0))
    assert len(responses.calls) == 0


@responses.activate
def test_get_device_ts_time_ago_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json={},
        status=500,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_device_ts_time_ago("device-1")

    assert "500" in str(exc_info.value)
