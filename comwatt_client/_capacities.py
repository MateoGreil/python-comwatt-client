from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class CapacitiesMixin(_BaseClient):
    def switch_capacity(self, capacity_id: int | str, enable: bool) -> dict[str, Any]:
        """
        Switch a specific capacity to the enable value.

        Args:
            capacity_id (int | str): The ID of the capacity.
            enable (bool): The target state.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._json_or_empty(self._request(
            "PUT", f"/capacities/{capacity_id}/switch?enable={str(enable).lower()}"
        ))

    def set_pilot_wire(self, capacity_id: int | str, state: str) -> dict[str, Any]:
        """
        Sets the pilot-wire order of a heating capacity.

        The capacity must be a "select" capacity: on a non-select capacity the
        request is rejected with 412 `capacity.is.not.a.select`
        (live-verified 2026-10-27).

        Args:
            capacity_id (int | str): The numeric id of the capacity (the `id` field,
                not the opaque `capacityId` string).
            state (str): The pilot-wire order to apply. Not server-side
                enum-bound: the 2026-10-27 binding sweep passed any string, so
                the valid orders remain unverified (no pilot-wire hardware on
                the probe account). Inspect the capacity's `selectValues` field
                for the orders valid on your hardware.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._json_or_empty(self._request(
            "PUT", f"/capacities/{capacity_id}/pilot-wire", params={"state": state}
        ))

    def set_thermal_mode(self, capacity_id: int | str, state: str) -> dict[str, Any]:
        """
        Sets the thermal mode of a thermostat capacity.

        The capacity must be a "select" capacity: on a non-select capacity the
        request is rejected with 412 `capacity.is.not.a.select`
        (live-verified 2026-10-27).

        Args:
            capacity_id (int | str): The numeric id of the capacity (the `id` field,
                not the opaque `capacityId` string).
            state (str): The thermal mode to apply. One of `OFF`, `HEAT`, `COOL`
                (live-pinned 2026-10-27 by an enum-binding sweep of 42
                candidates; any other value is rejected with
                400 "Failed to convert 'state' with value: '…'"). Inspect the
                capacity's `selectValues` field for the values valid on your
                hardware.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._json_or_empty(self._request(
            "PUT", f"/capacities/{capacity_id}/thermal-mode", params={"state": state}
        ))

    def set_thermostat_set_point(self, capacity_id: int | str, value: float | int) -> dict[str, Any]:
        """
        Sets the target set-point of a thermostat capacity.

        Args:
            capacity_id (int | str): The numeric id of the capacity (the `id` field,
                not the opaque `capacityId` string).
            value (float | int): The target set-point (e.g. a temperature).
                Passed through to the API as-is; the accepted range/unit is
                defined by the backend and was not confirmed against a live
                thermostat.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._json_or_empty(self._request(
            "PUT", f"/capacities/{capacity_id}/thermostat-set-point", params={"value": value}
        ))


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

    def set_thermal_control(
        self,
        thermal_control_id: int | str,
        device_id: int | str,
        set_point: float | int | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """
        Updates the thermal-control configuration (set-point / mode) of
        the specified device.

        Live-verified 2026-10-27 (enum-binding oracle on a nonexistent
        id): the inline `device` object requires the Jackson
        discriminator `"@class": "Device"` plus the numeric id (without
        it the API answers 400 "Failed to read request"), so the id is
        coerced with `int()` to accept string ids (non-numeric strings
        raise `ValueError`); `device` is the only required field;
        `setPoint` / `mode` are optional; and validation runs before
        the path lookup. The `{id}` path
        parameter is the thermal-control config id (a device id 404s),
        obtained from `get_thermal_control(device_id)` on devices that
        have one. The success path is unverified (no thermal-control
        config exists on the probe account); `mode` values are
        unconfirmed at this endpoint (the capacity-level thermal-mode
        enum is OFF/HEAT/COOL, see `set_thermal_mode`).

        Args:
            thermal_control_id (int | str): The ID of the
                thermal-control configuration (the `{id}` path
                parameter; a device id 404s).
            device_id (int | str): The ID of the device, embedded in
                the body's `device` object.
            set_point (float | int | None): The target set-point.
                Sent only when not None. Defaults to None.
            mode (str | None): The target mode. Sent only when not
                None; accepted values are unconfirmed at this endpoint
                (the capacity-level thermal-mode enum is OFF/HEAT/COOL).
                Defaults to None.

        Returns:
            dict: A dictionary containing the response from the API.

        Raises:
            ComwattAPIError: If the API responds with an unexpected status.

        """
        payload: dict[str, Any] = {
            "device": {"@class": "Device", "id": int(device_id)}
        }
        if set_point is not None:
            payload["setPoint"] = set_point
        if mode is not None:
            payload["mode"] = mode
        return self._json_or_empty(self._request(
            "PUT", f"/thermalcontrol/{thermal_control_id}", json=payload
        ))
