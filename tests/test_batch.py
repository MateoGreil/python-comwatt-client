import json
import time

import pytest
import responses

import comwatt_client._aggregations as aggregations_module
from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


def _add_device_response(device_id, body, *, status=200, extra_params=None, delay=0.0):
    params = {"id": device_id}
    if extra_params:
        params.update(extra_params)

    def _callback(request):
        if delay:
            time.sleep(delay)
        return (status, {}, json.dumps(body))

    responses.add_callback(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        callback=_callback,
        content_type="application/json",
        match=[responses.matchers.query_param_matcher(params, strict_match=False)],
    )


@responses.activate
def test_get_devices_ts_time_ago_preserves_input_order_with_staggered_completion(client):
    device_ids = ["device-3", "device-1", "device-2"]
    bodies = {
        "device-3": {"series": [3]},
        "device-1": {"series": [1]},
        "device-2": {"series": [2]},
    }

    _add_device_response("device-3", bodies["device-3"], delay=0.05)
    _add_device_response("device-1", bodies["device-1"])
    _add_device_response("device-2", bodies["device-2"])

    result = client.get_devices_ts_time_ago(device_ids)

    assert result == [bodies["device-3"], bodies["device-1"], bodies["device-2"]]


@responses.activate
def test_get_devices_ts_time_ago_kwargs_passthrough(client):
    device_ids = ["device-1", "device-2"]
    bodies = {"device-1": {"series": [1]}, "device-2": {"series": [2]}}

    for device_id in device_ids:
        _add_device_response(
            device_id,
            bodies[device_id],
            extra_params={"measureKind": "QUANTITY", "aggregationLevel": "DAY"},
        )

    result = client.get_devices_ts_time_ago(
        device_ids, measure_kind="QUANTITY", aggregation_level="DAY"
    )

    assert result == [bodies["device-1"], bodies["device-2"]]
    assert len(responses.calls) == 2


@responses.activate
def test_get_devices_ts_time_ago_fail_fast_picks_first_failure_in_input_order(client):
    device_ids = ["device-1", "device-2", "device-3", "device-4"]

    _add_device_response("device-1", {"series": [1]})
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json={"detail": "device-2 failed"},
        status=500,
        match=[responses.matchers.query_param_matcher({"id": "device-2"}, strict_match=False)],
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/aggregations/time-series",
        json={"detail": "device-3 failed"},
        status=502,
        match=[responses.matchers.query_param_matcher({"id": "device-3"}, strict_match=False)],
    )
    _add_device_response("device-4", {"series": [4]})

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_devices_ts_time_ago(device_ids)

    assert "device-2 failed" in str(exc_info.value)
    assert exc_info.value.status_code == 500
    assert len(responses.calls) == 4


@responses.activate
def test_get_devices_ts_time_ago_empty_list_returns_empty_without_requests(client):
    result = client.get_devices_ts_time_ago([])

    assert result == []
    assert len(responses.calls) == 0


@responses.activate
def test_get_devices_ts_time_ago_default_max_workers_is_capped_at_eight(client, monkeypatch):
    captured = {}
    real_executor = aggregations_module.ThreadPoolExecutor

    class RecordingExecutor(real_executor):
        def __init__(self, max_workers=None, *args, **kwargs):
            captured["max_workers"] = max_workers
            super().__init__(max_workers=max_workers, *args, **kwargs)

    monkeypatch.setattr(aggregations_module, "ThreadPoolExecutor", RecordingExecutor)

    device_ids = [f"device-{i}" for i in range(12)]
    for device_id in device_ids:
        _add_device_response(device_id, {"series": [1]})

    client.get_devices_ts_time_ago(device_ids)

    assert captured["max_workers"] == 8


@responses.activate
def test_get_devices_ts_time_ago_default_max_workers_matches_short_device_list(client, monkeypatch):
    captured = {}
    real_executor = aggregations_module.ThreadPoolExecutor

    class RecordingExecutor(real_executor):
        def __init__(self, max_workers=None, *args, **kwargs):
            captured["max_workers"] = max_workers
            super().__init__(max_workers=max_workers, *args, **kwargs)

    monkeypatch.setattr(aggregations_module, "ThreadPoolExecutor", RecordingExecutor)

    device_ids = ["device-1", "device-2", "device-3"]
    for device_id in device_ids:
        _add_device_response(device_id, {"series": [1]})

    client.get_devices_ts_time_ago(device_ids)

    assert captured["max_workers"] == 3


@responses.activate
def test_get_devices_ts_time_ago_explicit_max_workers_is_respected(client, monkeypatch):
    captured = {}
    real_executor = aggregations_module.ThreadPoolExecutor

    class RecordingExecutor(real_executor):
        def __init__(self, max_workers=None, *args, **kwargs):
            captured["max_workers"] = max_workers
            super().__init__(max_workers=max_workers, *args, **kwargs)

    monkeypatch.setattr(aggregations_module, "ThreadPoolExecutor", RecordingExecutor)

    device_ids = [f"device-{i}" for i in range(5)]
    for device_id in device_ids:
        _add_device_response(device_id, {"series": [1]})

    client.get_devices_ts_time_ago(device_ids, max_workers=2)

    assert captured["max_workers"] == 2
