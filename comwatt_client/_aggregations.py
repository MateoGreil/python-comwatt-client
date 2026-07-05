from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ._core import _BaseClient


def _format_timestamp(value: datetime | str) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, str):
        return value
    raise TypeError(f"Expected datetime or str, got {type(value).__name__}")


def _aggregations_query(*, id_param: str, id_value: int | str, aggregation_level: str,
        measure_kind: str | None = None, aggregation_type: str | None = None,
        time_ago_unit: str | None = None, time_ago_value: int | str | None = None,
        start: datetime | str | None = None, end: datetime | str | None = None) -> dict[str, str]:
    if end is not None and start is None:
        raise ValueError("end requires start")

    params: dict[str, str] = {id_param: str(id_value), "aggregationLevel": aggregation_level}

    if measure_kind is not None:
        params["measureKind"] = measure_kind
    if aggregation_type is not None:
        params["aggregationType"] = aggregation_type

    if start is not None:
        params["start"] = _format_timestamp(start)
        if end is not None:
            params["end"] = _format_timestamp(end)
    else:
        if time_ago_unit is not None:
            params["timeAgoUnit"] = time_ago_unit
        if time_ago_value is not None:
            params["timeAgoValue"] = str(time_ago_value)

    return params


class AggregationsMixin(_BaseClient):
    def get_site_networks_ts_time_ago(self, site_id: int | str,
            measure_kind: str = "FLOW",
            aggregation_level: str = "NONE",
            aggregation_type: str | None = None,
            time_ago_unit: str = "HOUR",
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the time series data for the networks of a specific site, based on the provided parameters.

        Args:
            site_id (str): The ID of the site.
            measure_kind (str): The kind of measure (default: "FLOW").
            aggregation_level (str): The aggregation level (default: "NONE").
            aggregation_type (str): The aggregation type (default: None, can be : None, "SUM", "MAX").
            time_ago_unit (str): The unit of time ago (default: "HOUR").
            time_ago_value (int): The value of time ago (default: 1).
            start (datetime | str): The start of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                When provided, the relative `time_ago_unit`/`time_ago_value` parameters are ignored.
            end (datetime | str): The end of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                Defaults server-side to "now" when omitted. Passing `end` without `start` raises `ValueError`.

        Returns:
            dict: The time series data.

        Raises:
            ValueError: If `end` is given without `start`.
            Exception: If an error occurs while retrieving the data.

        """

        params = _aggregations_query(
            id_param="siteId", id_value=site_id, aggregation_level=aggregation_level,
            measure_kind=measure_kind, aggregation_type=aggregation_type,
            time_ago_unit=time_ago_unit, time_ago_value=time_ago_value,
            start=start, end=end,
        )

        return self._request("GET", "/aggregations/site-networks-ts-time-ago", params=params).json()

    def get_site_consumption_breakdown_time_ago(self, site_id: int | str,
            aggregation_level: str = "HOUR",
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the consumption breakdown data for a specific site, based on the provided parameters.

        Args:
            site_id (str): The ID of the site.
            aggregation_level (str): The aggregation level (default: "HOUR").
            time_ago_unit (str): The unit of time ago (default: "DAY").
            time_ago_value (int): The value of time ago (default: 1).
            start (datetime | str): The start of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                When provided, the relative `time_ago_unit`/`time_ago_value` parameters are ignored.
            end (datetime | str): The end of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                Defaults server-side to "now" when omitted. Passing `end` without `start` raises `ValueError`.

        Returns:
            dict: The consumption breakdown data.

        Raises:
            ValueError: If `end` is given without `start`.
            Exception: If an error occurs while retrieving the data.

        """

        params = _aggregations_query(
            id_param="siteId", id_value=site_id, aggregation_level=aggregation_level,
            time_ago_unit=time_ago_unit, time_ago_value=time_ago_value,
            start=start, end=end,
        )

        return self._request("GET", "/aggregations/consumption-breakdown-time-ago", params=params).json()

    def get_device_ts_time_ago(self, device_id: int | str,
            measure_kind: str = "FLOW",
            aggregation_level: str = "HOUR",
            aggregation_type: str = "MAX",
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = "1",
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the time series data for a specific device, based on the provided parameters.

        Args:
            device_id (str): The ID of the device.
            measure_kind (str): The kind of measure (default: "FLOW").
            aggregation_level (str): The aggregation level (default: "HOUR").
            aggregation_type (str): The aggregation type (default: "MAX").
            time_ago_unit (str): The unit of time ago (default: "DAY").
            time_ago_value (str): The value of time ago (default: "1").
            start (datetime | str): The start of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                When provided, the relative `time_ago_unit`/`time_ago_value` parameters are ignored.
            end (datetime | str): The end of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                Defaults server-side to "now" when omitted. Passing `end` without `start` raises `ValueError`.

        Returns:
            dict: The time series data.

        Raises:
            ValueError: If `end` is given without `start`.
            Exception: If an error occurs while retrieving the data.

        """

        params = _aggregations_query(
            id_param="id", id_value=device_id, aggregation_level=aggregation_level,
            measure_kind=measure_kind, aggregation_type=aggregation_type,
            time_ago_unit=time_ago_unit, time_ago_value=time_ago_value,
            start=start, end=end,
        )

        return self._request("GET", "/aggregations/time-series", params=params).json()

    def get_site_time_series(self, site_id: int | str,
            measure_kind: str = "FLOW",
            aggregation_level: str = "HOUR",
            aggregation_type: str | None = None,
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the whole-site rollup time series data for a specific site, based on the provided parameters.

        Args:
            site_id (str): The ID of the site.
            measure_kind (str): The kind of measure (default: "FLOW").
            aggregation_level (str): The aggregation level (default: "HOUR").
            aggregation_type (str): The aggregation type (default: None, can be : None, "SUM", "MAX").
            time_ago_unit (str): The unit of time ago (default: "DAY").
            time_ago_value (int): The value of time ago (default: 1).
            start (datetime | str): The start of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                When provided, the relative `time_ago_unit`/`time_ago_value` parameters are ignored.
            end (datetime | str): The end of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                Defaults server-side to "now" when omitted. Passing `end` without `start` raises `ValueError`.

        Returns:
            dict: The site-level time series data (productions, consumptions, injections, withdrawals,
                charges, discharges and rate series).

        Raises:
            ValueError: If `end` is given without `start`.
            Exception: If an error occurs while retrieving the data.

        """

        params = _aggregations_query(
            id_param="id", id_value=site_id, aggregation_level=aggregation_level,
            measure_kind=measure_kind, aggregation_type=aggregation_type,
            time_ago_unit=time_ago_unit, time_ago_value=time_ago_value,
            start=start, end=end,
        )

        return self._request("GET", "/aggregations/site-time-series", params=params).json()

    def get_top_consumption(self, site_id: int | str,
            aggregation_level: str = "DAY",
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the per-device consumption breakdown for a specific site, based on the provided parameters.

        Args:
            site_id (str): The ID of the site.
            aggregation_level (str): The aggregation level (default: "DAY").
            time_ago_unit (str): The unit of time ago (default: "DAY").
            time_ago_value (int): The value of time ago (default: 1).
            start (datetime | str): The start of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                When provided, the relative `time_ago_unit`/`time_ago_value` parameters are ignored.
            end (datetime | str): The end of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                Defaults server-side to "now" when omitted. Passing `end` without `start` raises `ValueError`.

        Returns:
            dict: The per-device consumption breakdown (top 5 devices by percentage plus an "others" bucket).

        Raises:
            ValueError: If `end` is given without `start`.
            Exception: If an error occurs while retrieving the data.

        """

        params = _aggregations_query(
            id_param="id", id_value=site_id, aggregation_level=aggregation_level,
            time_ago_unit=time_ago_unit, time_ago_value=time_ago_value,
            start=start, end=end,
        )

        return self._request("GET", "/aggregations/top-consumption", params=params).json()
