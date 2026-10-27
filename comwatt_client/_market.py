from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class MarketMixin(_BaseClient):
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

    def get_electricity_contract(self, site_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves the electricity contract(s) of a given site.

        The path parameter is the **numeric site id** (not the `siteUid`),
        no query parameter is involved, and the response is a JSON array —
        `[]` when the site has no contract (verified live 2026-09-06).

        Note: the server does not 404 on an unknown id; it returns `200 []`
        on the probe account regardless of the path segment, so the
        "site id" semantics rest on the SPA bundle (which builds the URL from
        the site id), not on server-side validation. The non-empty array
        shape is unverified: the probe site carries no contract.

        Args:
            site_id (int | str): The numeric ID of the site.

        Returns:
            list: A list of contract objects (`[]` when the site has none).

        Raises:
            ComwattAPIError: If the API responds with an unexpected status.

        """
        return self._request("GET", f"/electricitycontract/{site_id}").json()

    def get_electricity_contract_providers(self) -> list[str]:
        """
        Retrieves the flat list of electricity provider names the app knows
        about (`EDF`, `TotalEnergies`, `Octopus`, `Mint`, `Ekwateur`, …).

        Args:
            None

        Returns:
            list: A list of provider name strings.

        Raises:
            ComwattAPIError: If the API responds with an unexpected status.

        """
        return self._request("GET", "/electricitycontract/providers").json()
