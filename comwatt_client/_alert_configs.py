from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class AlertConfigsMixin(_BaseClient):
    def get_alert_configs(self, device_id: int | str) -> dict[str, Any]:
        """
        Retrieves the alert config (consumption threshold) of the specified
        device.

        Returns a single object `{period, id, min, max, activated,
        deviceId}` — the endpoint always answers 200, even when no alert is
        configured for the device: the response is then a skeleton object
        (`id`, `min`, `max` and `deviceId` are null, `activated` is False)
        rather than a 404. `min` and `max` are independently nullable;
        observed `period` values: `SLIDING_24_HOURS`. `device_id` is
        mandatory: the server rejects the request with 400 when it is
        missing.

        Args:
            device_id (int | str): The ID of the device.

        Returns:
            dict: The alert config object for the device.

        Raises:
            ComwattAPIError: If an error occurs while retrieving the alert
                config (400 if `device_id` is missing).

        """
        return self._request(
            "GET", f"/alertconfigs/v2?deviceId={device_id}"
        ).json()
