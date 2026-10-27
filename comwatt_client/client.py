from __future__ import annotations

from ._auth import AuthMixin
from ._alert_configs import AlertConfigsMixin
from ._aggregations import AggregationsMixin
from ._capacities import CapacitiesMixin
from ._catalogues import CataloguesMixin
from ._devices import DevicesMixin
from ._gateways import GatewaysMixin
from ._grid import GridMixin
from ._plannings import PlanningsMixin
from ._sites import SitesMixin
from ._typical_days import TypicalDaysMixin
from ._connected_objects import ConnectedObjectsMixin
from ._streaming import StreamingMixin
from ._electricity_contracts import ElectricityContractsMixin
from ._thermal_control import ThermalControlMixin
from ._weather import WeatherProxy


class ComwattClient(AuthMixin, AlertConfigsMixin, AggregationsMixin, CapacitiesMixin, CataloguesMixin, DevicesMixin, GatewaysMixin, GridMixin, PlanningsMixin, SitesMixin, ConnectedObjectsMixin, StreamingMixin, ElectricityContractsMixin, TypicalDaysMixin, ThermalControlMixin):
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
            auto_reauth (bool): Whether to keep the session alive
                automatically when credentials are available (default: True).
                Re-authenticates proactively before a request once the
                session expiry (see `session_expires_at`) is within 30
                seconds, and falls back to re-authenticating on a 401
                response (retrying the request once).

        Returns:
            None

        """

        super().__init__(timeout=timeout, auto_reauth=auto_reauth)
        self.weather = WeatherProxy(self)
