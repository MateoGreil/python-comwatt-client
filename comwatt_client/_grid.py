from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class GridMixin(_BaseClient):
    def get_electricity_price(self, site_id: int | str) -> dict[str, Any]:
        """
        Retrieves the EDF Tempo calendar / tariff structure for the specified site.

        Args:
            site_id (str): The ID of the site.

        Returns:
            dict: The Tempo tariff structure (`tempoSyntheses`, `daily`,
                `tempoSynthesesComplete`).

        Raises:
            Exception: If an error occurs while retrieving the electricity price.

        """
        return self._request("GET", f"/electricityprice?siteId={site_id}").json()

    def get_ecowatt(self) -> list[dict[str, Any]]:
        """
        Retrieves the RTE EcoWatt grid-stress forecast.

        Args:
            None

        Returns:
            list: A list of daily entries, each with a GREEN/ORANGE/RED status
                and a 24-entry hourly forecast.

        Raises:
            Exception: If an error occurs while retrieving the forecast.

        """

        return self._request("GET", "/ecowatt").json()
