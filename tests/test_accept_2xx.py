import responses

from tests.conftest import BASE_URL


@responses.activate
def test_request_accepts_201_on_read(client):
    responses.add(responses.GET, f"{BASE_URL}/devices/dev-1", json={"id": "dev-1"}, status=201)
    assert client.get_device("dev-1") == {"id": "dev-1"}


@responses.activate
def test_set_device_mode_accepts_201_with_body(client):
    responses.add(
        responses.PUT, f"{BASE_URL}/devices/dev-1/mode", json={"mode": "ON"}, status=201
    )
    assert client.set_device_mode("dev-1", "ON") == {"mode": "ON"}


@responses.activate
def test_switch_capacity_accepts_204_with_empty_body(client):
    responses.add(responses.PUT, f"{BASE_URL}/capacities/42/switch", body="", status=204)
    assert client.switch_capacity(42, True) == {}


@responses.activate
def test_set_thermal_control_accepts_204_with_empty_body(client):
    responses.add(responses.PUT, f"{BASE_URL}/thermalcontrol/7", body="", status=204)
    assert client.set_thermal_control(7, 1) == {}


@responses.activate
def test_update_planning_accepts_204_with_empty_body(client):
    responses.add(responses.PUT, f"{BASE_URL}/plannings/3", body="", status=204)
    assert client.update_planning(3, {"payload": True}) == {}


@responses.activate
def test_create_typical_day_accepts_204_with_empty_body(client):
    responses.add(responses.POST, f"{BASE_URL}/typicaldays", body="", status=204)
    assert client.create_typical_day("site-1", {"label": "x"}) == {}
