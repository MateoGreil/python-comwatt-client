from __future__ import annotations

from ._auth import AuthMixin
from ._aggregations import AggregationsMixin
from ._capacities import CapacitiesMixin
from ._devices import DevicesMixin
from ._grid import GridMixin
from ._sites import SitesMixin
from ._connected_objects import ConnectedObjectsMixin
from ._streaming import StreamingMixin


class ComwattClient(AuthMixin, AggregationsMixin, CapacitiesMixin, DevicesMixin, GridMixin, SitesMixin, ConnectedObjectsMixin, StreamingMixin):
    """
    A client for interacting with the Comwatt API.

    Args:
        None

    Attributes:
        base_url (str): The base URL of the Comwatt API.
        session (requests.Session): The session object for making HTTP requests.

    """
