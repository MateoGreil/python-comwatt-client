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

    def get_device_capacities(self, device_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves the capacities of a specific device.

        Unlike the site-wide listing (which deduplicates repeated entities
        into fastjson `@ref` pointers), this endpoint returns an array of
        full capacity objects.

        Each capacity has two ids: the numeric `id` (the primary key,
        expected by all `/capacities/{id}/...` methods such as
        `switch_capacity`), and the opaque `capacityId` string (the
        gateway-side identifier, echoed in WebSocket streaming frames).

        Args:
            device_id (str): The ID of the device.

        Returns:
            list: A list of the device's capacities.

        Raises:
            Exception: If an error occurs while retrieving the capacities.

        """
        return self._request("GET", f"/devices/{device_id}/capacities").json()

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

    def set_device_mode(self, device_id: int | str, mode: str) -> dict[str, Any]:
        """
        Sets the control mode of a specific device — the "Off / On / Auto"
        control.

        Observed mode values are "ON", "OFF" and "COMWATT" (COMWATT is the
        solar-driven auto mode, same family as the planning modes). They were
        observed read-only in typical-day / planning modes: no write-based
        enum validation was performed, and the write itself is not
        live-verified on a consenting device.

        The request shape comes from the SPA bundle and is likewise not
        live-verified: the mode is sent as a JSON body `{"mode": mode}`.
        If the API answers 400 live, the mode may instead be expected as a
        query parameter.

        Args:
            device_id (str): The ID of the device.
            mode (str): The control mode to apply ("ON", "OFF" or
                "COMWATT"). Passed through to the API as-is.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request(
            "PUT", f"/devices/{device_id}/mode", json={"mode": mode}
        ).json()
