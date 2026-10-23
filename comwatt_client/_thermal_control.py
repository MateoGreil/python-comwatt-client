from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class ThermalControlMixin(_BaseClient):
    def get_thermal_control(self, device_id: int | str) -> dict[str, Any] | None:
        """
        Retrieves the thermal-control configuration (set-point / mode) of
        the specified device.

        The endpoint answers 200 with an empty body when the device has no
        thermal control (e.g. non-thermal devices); the method then returns
        `None` rather than raising. The payload shape is unverified: no
        thermal or SG-Ready equipment exists on the probe site, so the keys
        returned by real thermostats and water heaters are presumed
        (set-point / mode) rather than observed.

        Args:
            device_id (int | str): The ID of the device.

        Returns:
            dict | None: The thermal-control object for the device, or
                `None` when the API answers 200 with an empty body.

        Raises:
            ComwattAPIError: If the API responds with an unexpected status.

        """
        response = self._request(
            "GET", f"/thermalcontrol?deviceId={device_id}"
        )
        if not response.text.strip():
            return None
        return response.json()
