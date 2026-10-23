from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class GatewaysMixin(_BaseClient):
    def get_gateway(self, gateway_id: int | str) -> dict[str, Any]:
        """
        Retrieves a gateway (the Comwatt box) by its numeric id.

        Takes the numeric `id` (from `gateway["id"]`), **not** the opaque
        `gatewayUid` string — the endpoint rejects it with a 400.

        The response is the full gateway document (JSON-with-refs: repeated
        entities appear as `{"@ref": "N"}` after their first `"@id": "N"`
        occurrence, and are returned as-is). The `connected`, `updating` and
        `status` fields are the "box offline / being updated" flags a health
        check wants.

        Args:
            gateway_id (int | str): The numeric ID of the gateway.

        Returns:
            dict: The gateway document.

        Raises:
            ComwattAPIError: If an error occurs while retrieving the gateway.

        """
        return self._request("GET", f"/gateways/{gateway_id}").json()

    def get_gateway_by_uid(self, gateway_uid: str) -> dict[str, Any]:
        """
        Retrieves a gateway by its opaque `gatewayUid` string.

        Takes the `gatewayUid` (from `gateway["gatewayUid"]`), **not** the
        numeric `id`. Returns the same gateway document as `get_gateway`
        (JSON-with-refs, returned as-is).

        Args:
            gateway_uid (str): The UID of the gateway.

        Returns:
            dict: The gateway document.

        Raises:
            ComwattAPIError: If an error occurs while retrieving the gateway.

        """
        return self._request(
            "GET", f"/gateways/by-gateway-uid/{gateway_uid}"
        ).json()

    def get_gateway_network(self, gateway_uid: str) -> dict[str, Any]:
        """
        Retrieves the network details of a gateway.

        ⚠ Despite the URL path, this endpoint takes the **`gatewayUid`**
        string, not the numeric `id`: passing the numeric id answers 412
        `gateway.not.found.for.fetching.network.details` (and that error
        body is a bare JSON array, so `detail` is None on the raised
        error).

        Useful for a "box offline / weak Wi-Fi" check (signal strength,
        channel, ...).

        Args:
            gateway_uid (str): The UID of the gateway.

        Returns:
            dict: The gateway document enriched with network details.

        Raises:
            ComwattAPIError: If an error occurs while retrieving the network
                details (412 if a numeric id is passed instead of the uid).

        """
        return self._request("GET", f"/gateways/{gateway_uid}/network").json()

    def get_gateway_ssids(self, gateway_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves the Wi-Fi networks visible to a gateway.

        Takes the numeric `id` (from `gateway["id"]`), **not** the
        `gatewayUid` string — the endpoint rejects it with a 400.

        ⚠ The response includes **neighbouring** Wi-Fi networks (other
        people's SSIDs), not just the gateway's own — treat it as
        privacy-sensitive data.

        Args:
            gateway_id (int | str): The numeric ID of the gateway.

        Returns:
            list: The Wi-Fi networks visible to the gateway.

        Raises:
            ComwattAPIError: If an error occurs while retrieving the SSIDs.

        """
        return self._request("GET", f"/gateways/{gateway_id}/ssids").json()
