import pytest
import responses

from comwatt_client import ComwattAPIError, ComwattAuthError, ComwattError
from tests.conftest import BASE_URL


@responses.activate
def test_get_sites_401_raises_auth_error(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/sites",
        json={},
        status=401,
    )

    with pytest.raises(ComwattAuthError):
        client.get_sites()


@responses.activate
def test_api_error_exposes_status_code_url_and_detail(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices",
        json={"detail": "Internal Server Error", "status": 500},
        status=500,
        content_type="application/problem+json",
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_devices("site-1")

    exc = exc_info.value
    assert exc.status_code == 500
    assert exc.url.endswith("/api/devices?siteId=site-1")
    assert exc.detail == "Internal Server Error"


def test_exception_hierarchy():
    assert issubclass(ComwattAuthError, ComwattError)
    assert issubclass(ComwattAPIError, ComwattError)
    assert issubclass(ComwattError, Exception)


@responses.activate
def test_bare_array_error_surfaces_code_as_detail(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/users/1/refreshtoken",
        json=[
            {
                "codes": ["user.already.activated"],
                "arguments": [],
                "defaultMessage": None,
                "objectName": "",
                "code": "user.already.activated",
            }
        ],
        status=412,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client._request("GET", "/users/1/refreshtoken")

    exc = exc_info.value
    assert exc.status_code == 412
    assert exc.detail == "user.already.activated"
    assert "user.already.activated" in str(exc)


@responses.activate
def test_bare_array_error_joins_multiple_codes(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices",
        json=[
            {"code": "first.error", "codes": ["first.error"], "defaultMessage": None},
            {"code": "second.error", "codes": ["second.error"], "defaultMessage": None},
        ],
        status=412,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_devices("site-1")

    assert exc_info.value.detail == "first.error, second.error"


@responses.activate
def test_bare_array_error_falls_back_to_codes_then_default_message(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices",
        json=[
            {"codes": ["fallback.code"], "defaultMessage": None},
            {"codes": [], "defaultMessage": "human readable default"},
            {"codes": [], "defaultMessage": None},
        ],
        status=412,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_devices("site-1")

    assert exc_info.value.detail == "fallback.code, human readable default"


@responses.activate
def test_modbus_bare_array_error_surfaces_human_message(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/connectedobjects/123/state-history",
        json=[
            {
                "codes": ["No Modbus configuration associated with ConnectedObject id: 123"],
                "arguments": [],
                "defaultMessage": None,
                "objectName": "",
                "code": "No Modbus configuration associated with ConnectedObject id: 123",
            }
        ],
        status=404,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client._request("GET", "/connectedobjects/123/state-history")

    assert exc_info.value.detail == "No Modbus configuration associated with ConnectedObject id: 123"


@responses.activate
def test_bare_array_error_without_usable_entries_gives_no_detail(client):
    responses.add(
        responses.GET,
        f"{BASE_URL}/devices",
        json=[{"codes": [], "defaultMessage": None}, "not-a-dict"],
        status=412,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.get_devices("site-1")

    assert exc_info.value.detail is None
