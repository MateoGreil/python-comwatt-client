from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, cast

from ._core import _BaseClient

if TYPE_CHECKING:
    from ._aggregations import AggregationsMixin


class BatchMixin(_BaseClient):
    def get_devices_ts_time_ago(self, device_ids: list[int | str], *,
            max_workers: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Retrieves the time series data for multiple devices concurrently.

        Fans `get_device_ts_time_ago(device_id, **kwargs)` out over a
        `concurrent.futures.ThreadPoolExecutor`, submitting one call per
        device. The client's `requests.Session` is shared across the worker
        threads: each call is a simple, independent GET, and `urllib3`'s
        connection pool is thread-safe in practice, but this is not an
        official guarantee of `requests` itself.

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
        agg_self = cast("AggregationsMixin", self)

        results: list[dict[str, Any] | None] = [None] * len(device_ids)
        errors: list[Exception | None] = [None] * len(device_ids)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(agg_self.get_device_ts_time_ago, device_id, **kwargs)
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
