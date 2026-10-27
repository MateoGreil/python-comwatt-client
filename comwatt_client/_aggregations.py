from __future__ import annotations

import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, cast

from ._core import _BaseClient
from ._series import normalize_time_series


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
        start: datetime | str | None = None, end: datetime | str | None = None,
        site_network_type: str | None = None) -> dict[str, str]:
    if end is not None and start is None:
        raise ValueError("end requires start")

    params: dict[str, str] = {id_param: str(id_value), "aggregationLevel": aggregation_level}

    if site_network_type is not None:
        params["siteNetworkType"] = site_network_type
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
            site_id (int | str): The ID of the site.
            measure_kind, aggregation_level, aggregation_type, time_ago_unit,
                time_ago_value, start, end: Shared time-window parameters —
                see `get_device_ts_time_ago`, the canonical holder of their
                documentation and live-pinned enums (this alias defaults
                `aggregation_level` to "NONE" and `time_ago_unit` to "HOUR").

        Returns:
            dict: The time series data. Numeric series are normalized to float/None
                samples; timestamps are left untouched.

        Raises:
            ValueError: If `end` is given without `start`.
            Exception: If an error occurs while retrieving the data.

        .. deprecated::
            Use :meth:`get_site_time_series` instead. The
            ``site-networks-ts-time-ago`` endpoint still responds, but the app
            has moved to ``site-time-series``; this alias is kept only for
            backward compatibility.

        """

        warnings.warn(
            "get_site_networks_ts_time_ago() is deprecated and will be removed in a "
            "future release; use get_site_time_series() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        params = _aggregations_query(
            id_param="siteId", id_value=site_id, aggregation_level=aggregation_level,
            measure_kind=measure_kind, aggregation_type=aggregation_type,
            time_ago_unit=time_ago_unit, time_ago_value=time_ago_value,
            start=start, end=end,
        )

        return normalize_time_series(
            self._request("GET", "/aggregations/site-networks-ts-time-ago", params=params).json()
        )

    def get_site_consumption_breakdown_time_ago(self, site_id: int | str,
            aggregation_level: str = "HOUR",
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the consumption breakdown data for a specific site, based on the provided parameters.

        Args:
            site_id (int | str): The ID of the site.
            aggregation_level, time_ago_unit, time_ago_value, start, end:
                Shared time-window parameters — see `get_device_ts_time_ago`,
                the canonical holder of their documentation and live-pinned
                enums.

        Returns:
            dict: The consumption breakdown data.

        Raises:
            ValueError: If `end` is given without `start`.
            Exception: If an error occurs while retrieving the data.

        .. deprecated::
            Use :meth:`get_top_consumption` instead. The
            ``consumption-breakdown-time-ago`` endpoint still responds, but the
            app has moved to ``top-consumption``; this alias is kept only for
            backward compatibility.

        """

        warnings.warn(
            "get_site_consumption_breakdown_time_ago() is deprecated and will be "
            "removed in a future release; use get_top_consumption() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

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
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the time series data for a specific device, based on the provided parameters.

        This method is the canonical holder of the shared time-window
        parameter documentation (`measure_kind`, `aggregation_level`,
        `aggregation_type`, `time_ago_unit`, `time_ago_value`, `start`,
        `end`); the other aggregation methods reference it.

        Args:
            device_id (int | str): The ID of the device.
            measure_kind (str): The kind of measure (default: "FLOW"). One of
                "FLOW", "QUANTITY", "STATE", "VALUE", "INDEX", "RATE"
                (live-pinned 2026-10-11; e.g. "POWER" or "TEMPERATURE" are
                rejected with 400).
            aggregation_level (str): The aggregation level (default: "HOUR"). One of
                "NONE", "HOUR", "DAY", "MONTH", "YEAR"; the API rejects "WEEK".
            aggregation_type (str): The aggregation type (default: "MAX"). One
                of "NONE", "MIN", "MAX", "SUM", "AVERAGE" (live-pinned
                2026-10-11; "AVG" is rejected with 400).
            time_ago_unit (str): The unit of time ago (default: "DAY"). One of
                "HOUR", "DAY", "WEEK", "MONTH", "YEAR".
            time_ago_value (int | str): The value of time ago (default: 1).
            start (datetime | str): The start of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                When provided, the relative `time_ago_unit`/`time_ago_value` parameters are ignored.
            end (datetime | str): The end of an absolute time window (default: None).
                Accepts a `datetime` or an ISO-8601 string; a naive `datetime` is treated as UTC.
                Defaults server-side to "now" when omitted. Passing `end` without `start` raises `ValueError`.

        Returns:
            dict: The time series data. Numeric series are normalized to float/None
                samples; timestamps are left untouched.

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

        return normalize_time_series(
            self._request("GET", "/aggregations/time-series", params=params).json()
        )

    def get_devices_ts_time_ago(self, device_ids: list[int | str], *,
            max_workers: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Retrieves the time series data for multiple devices concurrently.

        Fans `get_device_ts_time_ago(device_id, **kwargs)` out over a
        `concurrent.futures.ThreadPoolExecutor`, submitting one call per
        device. The client's `requests.Session` is shared across the worker
        threads: each call is a simple, independent GET, and `urllib3`'s
        connection pool is thread-safe in practice, but this is not an
        official guarantee of `requests` itself. Concurrent re-auth is
        serialized: at most one login runs, and the workers waiting on
        it retry with the refreshed session.

        Args:
            device_ids (list): The IDs of the devices to query.
            max_workers (int): The maximum number of worker threads
                (default: None, which uses `min(8, len(device_ids))`).
            **kwargs: Additional keyword arguments forwarded as-is to
                `get_device_ts_time_ago` for every device (e.g.
                `measure_kind`, `aggregation_level`, `start`, `end`).

        Returns:
            list: The time series data for each device, in the same order
                as `device_ids`. Empty if `device_ids` is empty (no
                executor is created in that case).

        Raises:
            ValueError: If `end` is given without `start` (raised by the
                per-device call).
            Exception: If one or more per-device calls fail, all calls are
                still awaited and the exception of the first failing
                device in `device_ids` order is raised.

        """

        if not device_ids:
            return []

        workers = max_workers if max_workers is not None else min(8, len(device_ids))

        results: list[dict[str, Any] | None] = [None] * len(device_ids)
        errors: list[Exception | None] = [None] * len(device_ids)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self.get_device_ts_time_ago, device_id, **kwargs)
                for device_id in device_ids
            ]
            for index, future in enumerate(futures):
                try:
                    results[index] = future.result()
                except Exception as exc:
                    errors[index] = exc

        for error in errors:
            if error is not None:
                raise error

        return cast("list[dict[str, Any]]", results)

    def get_site_network_time_series(self, site_id: int | str,
            site_network_type: str,
            measure_kind: str = "FLOW",
            aggregation_level: str = "HOUR",
            aggregation_type: str | None = None,
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the time series of one of a site's virtual "networks"
        (production, consumption, grid injection/withdrawal, battery charge
        or discharge), based on the provided parameters.

        Uses the site-addressed `siteNetworkType` overload of the
        `time-series` endpoint: the `id` query parameter carries the
        **numeric site id**, and the chosen network replaces the whole-site
        rollup (live-verified 2026-10-11).

        Args:
            site_id (int | str): The numeric ID of the site.
            site_network_type (str): The virtual network to read. One of
                "PRODUCTION", "CONSUMPTION", "INJECTION", "WITHDRAWAL",
                "CHARGE", "DISCHARGE" (live-pinned 2026-10-11). "CHARGE" /
                "DISCHARGE" select the battery flows; "BATTERY" and "GRID"
                are rejected with 400 — use the directional values.
            measure_kind, aggregation_level, aggregation_type, time_ago_unit,
                time_ago_value, start, end: Shared time-window parameters —
                see `get_device_ts_time_ago`, the canonical holder of their
                documentation and live-pinned enums.

        Returns:
            dict: The time series data. Numeric series are normalized to float/None
                samples; timestamps are left untouched.

        Raises:
            ValueError: If `end` is given without `start`.
            ComwattAPIError: If the API responds with an unexpected status.

        """
        params = _aggregations_query(
            id_param="id", id_value=site_id, aggregation_level=aggregation_level,
            measure_kind=measure_kind, aggregation_type=aggregation_type,
            time_ago_unit=time_ago_unit, time_ago_value=time_ago_value,
            start=start, end=end, site_network_type=site_network_type,
        )

        return normalize_time_series(
            self._request("GET", "/aggregations/time-series", params=params).json()
        )

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
            site_id (int | str): The ID of the site.
            measure_kind, aggregation_level, aggregation_type, time_ago_unit,
                time_ago_value, start, end: Shared time-window parameters —
                see `get_device_ts_time_ago`, the canonical holder of their
                documentation and live-pinned enums.

        Returns:
            dict: The site-level time series data (productions, consumptions, injections, withdrawals,
                charges, discharges and rate series). Numeric series are normalized to
                float/None samples; timestamps are left untouched.

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

        return normalize_time_series(
            self._request("GET", "/aggregations/site-time-series", params=params).json()
        )

    def get_top_consumption(self, site_id: int | str,
            aggregation_level: str = "DAY",
            time_ago_unit: str = "DAY",
            time_ago_value: int | str = 1,
            start: datetime | str | None = None,
            end: datetime | str | None = None) -> dict[str, Any]:
        """
        Retrieves the per-device consumption breakdown for a specific site, based on the provided parameters.

        Args:
            site_id (int | str): The ID of the site.
            aggregation_level, time_ago_unit, time_ago_value, start, end:
                Shared time-window parameters — see `get_device_ts_time_ago`,
                the canonical holder of their documentation and live-pinned
                enums (this method defaults `aggregation_level` to "DAY").

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
