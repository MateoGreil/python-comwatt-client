from __future__ import annotations

from ._auth import AuthMixin
from ._aggregations import AggregationsMixin
from ._capacities import CapacitiesMixin
from ._devices import DevicesMixin
from ._grid import GridMixin
from ._sites import SitesMixin
from ._connected_objects import ConnectedObjectsMixin
from ._streaming import StreamingMixin
from ._electricity_contracts import ElectricityContractsMixin
from ._weather import WeatherProxy


class ComwattClient(AuthMixin, AggregationsMixin, CapacitiesMixin, DevicesMixin, GridMixin, SitesMixin, ConnectedObjectsMixin, StreamingMixin, ElectricityContractsMixin):
    """
    A client for interacting with the Comwatt API.

    Args:
        None

    Attributes:
        base_url (str): The base URL of the Comwatt API.
        session (requests.Session): The session object for making HTTP requests.
        weather (WeatherProxy): Namespaced access to the unauthenticated weather proxy.

    """

    def __init__(self, timeout: float = 30, auto_reauth: bool = True) -> None:
        """
        Initializes the Comwatt client.

        Args:
            timeout (float): The request timeout in seconds (default: 30).
            auto_reauth (bool): Whether to automatically re-authenticate on a
                401 response when credentials are available (default: True).

        Returns:
            None

        """

        super().__init__(timeout=timeout, auto_reauth=auto_reauth)
        self.weather = WeatherProxy(self)
