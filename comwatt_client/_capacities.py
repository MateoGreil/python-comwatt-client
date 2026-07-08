from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class CapacitiesMixin(_BaseClient):
    def switch_capacity(self, capacity_id: int | str, enable: bool) -> dict[str, Any]:
        """
        Switch a specific capacity to the enable value.

        Args:
            capacity_id (str): The ID of the capacity.
            enable (bool): The target state.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request("PUT", f"/capacities/{capacity_id}/switch?enable={str(enable).lower()}").json()

    def set_pilot_wire(self, capacity_id: int | str, state: str) -> dict[str, Any]:
        """
        Sets the pilot-wire order of a heating capacity.

        Args:
            capacity_id (str): The numeric id of the capacity (the `id` field,
                not the opaque `capacityId` string).
            state (str): The pilot-wire order to apply. Passed through to the API
                as-is; the accepted values are defined by the backend and were
                not confirmed against a live pilot-wire device. Inspect the
                capacity's `selectValues` field for the values valid on your
                hardware. Sending an unsupported value is likely to return 400.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request(
            "PUT", f"/capacities/{capacity_id}/pilot-wire", params={"state": state}
        ).json()

    def set_thermal_mode(self, capacity_id: int | str, state: str) -> dict[str, Any]:
        """
        Sets the thermal mode of a thermostat capacity (e.g. eco / comfort).

        Args:
            capacity_id (str): The numeric id of the capacity (the `id` field,
                not the opaque `capacityId` string).
            state (str): The thermal mode to apply. Passed through to the API
                as-is; the accepted values are defined by the backend and were
                not confirmed against a live thermostat. Inspect the capacity's
                `selectValues` field for the values valid on your hardware.
                Sending an unsupported value is likely to return 400.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request(
            "PUT", f"/capacities/{capacity_id}/thermal-mode", params={"state": state}
        ).json()

    def set_thermostat_set_point(self, capacity_id: int | str, value: float | int) -> dict[str, Any]:
        """
        Sets the target set-point of a thermostat capacity.

        Args:
            capacity_id (str): The numeric id of the capacity (the `id` field,
                not the opaque `capacityId` string).
            value (float | int): The target set-point (e.g. a temperature).
                Passed through to the API as-is; the accepted range/unit is
                defined by the backend and was not confirmed against a live
                thermostat.

        Returns:
            dict: A dictionary containing the response from the API.

        """
        return self._request(
            "PUT", f"/capacities/{capacity_id}/thermostat-set-point", params={"value": value}
        ).json()
