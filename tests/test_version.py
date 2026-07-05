import importlib.metadata

import comwatt_client


def test_version_is_nonempty_string():
    assert isinstance(comwatt_client.__version__, str)
    assert comwatt_client.__version__


def test_version_is_exported():
    assert "__version__" in comwatt_client.__all__


def test_version_matches_installed_metadata():
    assert comwatt_client.__version__ == importlib.metadata.version("comwatt-client")
