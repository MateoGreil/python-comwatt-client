from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class ConnectedObjectsMixin(_BaseClient):
    def get_connected_objects(self, site_id: int | str | None = None,
            gateway_uid: str | None = None) -> list[dict[str, Any]]:
        """
        Retrieves the connected objects for a site or a gateway.

        Exactly one of `site_id` or `gateway_uid` must be provided.

        Args:
            site_id (int | str): The ID of the site (default: None).
            gateway_uid (str): The UID of the gateway (default: None).

        Returns:
            list: A list of connected objects.

        Raises:
            ValueError: If neither or both of `site_id` and `gateway_uid` are provided.
            Exception: If an error occurs while retrieving the connected objects.

        """
        if (site_id is None) == (gateway_uid is None):
            raise ValueError(
                "Exactly one of 'site_id' or 'gateway_uid' must be provided."
            )

        if site_id is not None:
            path = f"/connectedobjects?siteId={site_id}"
        else:
            path = f"/connectedobjects?gatewayUid={gateway_uid}"

        return self._request("GET", path).json()

    def get_connected_object(self, connected_object_id: int | str) -> dict[str, Any]:
        """
        Retrieves information about a specific connected object.

        Args:
            connected_object_id (str): The ID of the connected object.

        Returns:
            dict: A dictionary containing the connected object information.

        Raises:
            Exception: If an error occurs while retrieving the connected object.

        """
        return self._request("GET", f"/connectedobjects/{connected_object_id}").json()

    def get_measure_keys(self, site_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves the measure keys (measurement inventory) for the specified site.

        Args:
            site_id (str): The ID of the site.

        Returns:
            list: A list of measure keys, each describing a (device, measureKind) pair
                with a stable numeric id and measureKey UUID.

        Raises:
            Exception: If an error occurs while retrieving the measure keys.

        """
        return self._request("GET", f"/measurekeys/measurekeys?siteId={site_id}").json()
