from __future__ import annotations

from typing import Any

from ._core import _BaseClient
from .exceptions import ComwattAPIError


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

    def set_alert_config(
        self,
        device_id: int | str,
        min: float | int | None,
        max: float | int | None,
        period: str = "SLIDING_24_HOURS",
        activated: bool = True,
    ) -> dict[str, Any]:
        """
        Sets the alert config (consumption threshold) of the specified
        device.

        Two-step flow: the numeric config id is first resolved with
        `get_alert_configs` (`GET /alertconfigs/v2?deviceId=`), then the
        update is sent as `PUT /alertconfigs/v2/{id}` with the JSON body
        `{deviceId, min, max, period, activated}`. The write body shape is
        derived from the web-app bundle, not live-verified.

        Devices without a configured alert answer the read step with a
        skeleton object (`id` null): there is no alert config to update,
        so a `ComwattAPIError` is raised — a PUT requires the existing
        config id, and the creation path (POST) is not exposed by this
        client.

        The `period` value observed read-side is `SLIDING_24_HOURS`; other
        values accepted by the write side are unverified. The parameter
        names `min` and `max` shadow the Python builtins to mirror the
        API body fields.

        Args:
            device_id (int | str): The ID of the device.
            min (float | int | None): The lower consumption threshold.
            max (float | int | None): The upper consumption threshold.
            period (str): The aggregation period; observed read-side:
                `SLIDING_24_HOURS`.
            activated (bool): Whether the alert is active.

        Returns:
            dict: The updated alert config object for the device.

        Raises:
            ComwattAPIError: If the device has no alert config to update
                (skeleton `id` null), or if an error occurs while updating
                the alert config.

        """
        config = self.get_alert_configs(device_id)
        config_id = config.get("id")
        if config_id is None:
            raise ComwattAPIError(
                f"Device {device_id} has no alert config to update: the "
                "read endpoint returned a skeleton object with a null id, "
                "and the update (PUT) requires the existing config id. The "
                "creation path (POST) is not exposed by this client."
            )
        return self._json_or_empty(self._request(
            "PUT",
            f"/alertconfigs/v2/{config_id}",
            json={
                "deviceId": device_id,
                "min": min,
                "max": max,
                "period": period,
                "activated": activated,
            },
        ))
