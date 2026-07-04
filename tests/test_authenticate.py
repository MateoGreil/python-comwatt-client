import json

import pytest
import responses

from comwatt_client import ComwattAuthError
from tests.conftest import BASE_URL


@responses.activate
def test_authenticate_success(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=200,
    )

    result = client.authenticate("testuser", "testpass")

    assert result is None
    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert request.method == "POST"
    assert request.url == f"{BASE_URL}/v1/authent"
    body = json.loads(request.body)
    assert body["username"] == "testuser"
    assert (
        body["password"]
        == "d5a29cd5189cb9409b478fd31350c43aba0db9a8d3116da1331a2cd1424a4579"
    )


@responses.activate
def test_authenticate_error(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/authent",
        json={},
        status=401,
    )

    with pytest.raises(ComwattAuthError) as exc_info:
        client.authenticate("testuser", "testpass")

    assert "401" in str(exc_info.value)
