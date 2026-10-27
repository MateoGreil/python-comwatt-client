from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class CataloguesMixin(_BaseClient):
    def get_products(self) -> list[dict[str, Any]]:
        """
        Retrieves the Comwatt hardware catalogue (`MONITOR_GEN_4`,
        `POWER_GEN_4`, ...).

        Args:
            None

        Returns:
            list: A list of product objects (`{id, name, brand, cardinality,
                features}`).

        Raises:
            ComwattAPIError: If the API responds with an unexpected status.

        """
        return self._request("GET", "/products").json()

    def get_timezones(self) -> list[dict[str, Any]]:
        """
        Retrieves the static list of timezones the app knows about.

        Each entry is a `{timeZone, posix}` pair (IANA name + POSIX TZ
        string), e.g. `{"timeZone": "Europe/Paris", "posix":
        "CET-1CEST,M3.5.0,M10.5.0/3"}`.

        Args:
            None

        Returns:
            list: A list of timezone objects.

        Raises:
            ComwattAPIError: If the API responds with an unexpected status.

        """
        return self._request("GET", "/util/timezones").json()

    def get_modbus_configurations(self) -> list[dict[str, Any]]:
        """
        Retrieves the Modbus configuration catalogue.

        Live-verified 2026-10-11: 4 entries on the probe account. Each entry
        describes one supported Modbus device family:

        ```json
        {
          "id": 1, "name": "huawei", "label": "Huaweï Sun2000 nKTL",
          "port": 502, "slave": 1,
          "device_kinds": ["SOLAR_PANEL", "BATTERY", "GRID_METER"]
        }
        ```

        Note the `device_kinds` key is snake_case, unlike the camelCase used
        everywhere else in the API. Modbus pairing itself is an installer
        flow (`POST /devices/v2/modbus`) and is not exposed here.

        Args:
            None

        Returns:
            list: A list of Modbus configuration objects.

        Raises:
            ComwattAPIError: If the API responds with an unexpected status.

        """
        return self._request("GET", "/gateways/modbus-configurations").json()
