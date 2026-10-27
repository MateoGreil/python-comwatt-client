import json

import pytest
import responses

from comwatt_client import ComwattAPIError
from tests.conftest import BASE_URL


@responses.activate
def test_paginate_rejects_params_with_existing_page_entry(client):
    with pytest.raises(ValueError, match="page"):
        client._paginate("/plannings", params={"page": 2})


@responses.activate
def test_paginate_accepts_page_like_param_names(client):
    responses.add(responses.GET, f"{BASE_URL}/plannings", json={"content": [{"a": 1}]})
    responses.add(responses.GET, f"{BASE_URL}/plannings", json={"content": []})

    assert client._paginate("/plannings", params={"somepage": 1}) == [{"a": 1}]


@responses.activate
def test_paginate_terminates_on_empty_page_without_total_pages(client):
    responses.add(responses.GET, f"{BASE_URL}/plannings", json={"content": [{"a": 1}]})
    responses.add(responses.GET, f"{BASE_URL}/plannings", json={"content": []})

    assert client._paginate("/plannings") == [{"a": 1}]


@responses.activate
def test_paginate_stops_at_page_cap_without_total_pages(client):
    def endless_page(request):
        return (200, {}, json.dumps({"content": [{"page": "never-empty"}]}))

    responses.add_callback(responses.GET, f"{BASE_URL}/plannings", callback=endless_page)

    with pytest.raises(ComwattAPIError, match="pagination"):
        client._paginate("/plannings")
