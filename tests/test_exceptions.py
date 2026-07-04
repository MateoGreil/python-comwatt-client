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
