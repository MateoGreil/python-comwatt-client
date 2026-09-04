"""Normalization of time-series payloads.

Some Comwatt accounts return the numeric series of the time-series endpoints
(``site-time-series``, ``time-series``, ``site-networks-ts-time-ago``) with
their samples serialized as JSON strings (e.g. ``"12.34"``) instead of JSON
numbers. ``normalize_time_series`` coerces those payloads to a uniform shape:
every list except ``timestamps`` contains only ``float`` or ``None`` samples.
"""

from __future__ import annotations

from typing import Any


def _coerce_sample(item: Any) -> Any:
    if item is None:
        return None
    if isinstance(item, bool):
        return None
    if isinstance(item, (int, float)):
        return float(item)
    if isinstance(item, str):
        try:
            return float(item.strip())
        except ValueError:
            return None
    return item


def normalize_time_series(payload: Any) -> Any:
    """Coerce the numeric series of a time-series payload to ``float | None``.

    Walks the top level of the response; every value that is a list, except
    the ``timestamps`` series, is mapped sample-by-sample:

    - JSON numbers become ``float``
    - numeric strings (e.g. ``"12.34"``) become ``float``
    - ``None`` stays ``None``
    - anything else usable as a number gap (empty or unparseable strings,
      booleans) becomes ``None``

    Non-list fields and unknown structures are returned unchanged, so extra
    metadata the API may add is never altered.
    """
    if not isinstance(payload, dict):
        return payload
    return {
        key: (
            value
            if key == "timestamps" or not isinstance(value, list)
            else [_coerce_sample(item) for item in value]
        )
        for key, value in payload.items()
    }
