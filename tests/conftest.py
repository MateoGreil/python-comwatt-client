import pytest

from comwatt_client import ComwattClient

BASE_URL = "https://energy.comwatt.com/api"


@pytest.fixture
def client():
    return ComwattClient()


@pytest.fixture
def client_no_reauth():
    return ComwattClient(auto_reauth=False)
