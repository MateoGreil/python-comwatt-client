from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class SitesMixin(_BaseClient):
    def get_authenticated_user(self) -> dict[str, Any]:
        """
        Retrieves information about the authenticated user.

        Args:
            None

        Returns:
            dict: Information about the authenticated user.

        Raises:
            Exception: If an error occurs while retrieving the information.

        """

        return self._request("GET", "/users/authenticated").json()

    def get_sites(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of sites associated with the authenticated user.

        Args:
            None

        Returns:
            list: A list of sites.

        Raises:
            Exception: If an error occurs while retrieving the sites.

        """

        return self._request("GET", "/sites").json()

    def get_tiles(self, site_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves the dashboard tile configuration for the specified site.

        This is configuration only (which tile of which type points at which
        device: `REAL_TIME` / `VALUATION` / `THIRD_PARTY`), not live measurement values.

        Args:
            site_id (str): The ID of the site.

        Returns:
            list: A list of tile configuration objects.

        Raises:
            Exception: If an error occurs while retrieving the tiles.

        """
        return self._request("GET", f"/tiles?siteId={site_id}").json()
