from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class DevicesMixin(_BaseClient):
    def get_devices(self, site_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves a list of devices for the specified site.

        Args:
            site_id (str): The ID of the site.

        Returns:
            list: A list of devices.

        Raises:
            Exception: If an error occurs while retrieving the devices.

        """

        return self._request("GET", f"/devices?siteId={site_id}").json()

    def get_device(self, device_id: int | str) -> dict[str, Any]:
        """
        Retrieves information about a specific device.

        Args:
            device_id (str): The ID of the device.

        Returns:
            dict: A dictionary containing the device information.

        """
        return self._request("GET", f"/devices/{device_id}").json()

    def put_device(self, device_id: int | str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Updates a specific device with the provided payload.

        Args:
            device_id (str): The ID of the device.
            payload (dict): The payload to update the device.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request("PUT", f"/devices/{device_id}", json=payload).json()

    def get_device_kinds(self, site_uid: str) -> list[dict[str, Any]]:
        """
        Retrieves the catalogue of device kinds available for a site (the
        "add a device" picker), with codes such as "SOLAR_PANEL", "GRID_METER"
        or "PRO_HEAT_PUMP".

        Args:
            site_uid (str): The short `siteUid` string of the site (e.g. "992179e1",
                found as `site["siteUid"]` in `get_sites()` output), NOT the numeric site id.

        Returns:
            list: A list of device-kind catalogue objects.

        Raises:
            Exception: If an error occurs while retrieving the device kinds.

        """
        return self._request("GET", f"/devicekinds/by-site-uid/{site_uid}").json()

    def switch_capacity(self, capacity_id: int | str, enable: bool) -> dict[str, Any]:
        """
        Switch a specific capcaity to the enable value.

        Args:
            capacity_id (str): The ID of the capacity.
            enable (bool): The target state.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request("PUT", f"/capacities/{capacity_id}/switch?enable={str(enable).lower()}").json()
