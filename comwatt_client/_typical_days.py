from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class TypicalDaysMixin(_BaseClient):
    def get_typical_days(self, site_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves the "typical day" templates for the specified site.

        These are the time-range templates (`ON` / `OFF` / `COMWATT`
        modes) that drive the auto-consumption optimizer and that
        plannings reference through their `typicalDaySchedules`.
        Auto-paginates: fetches every `?page=` and returns the
        concatenated `content` of all pages as a flat list.

        Args:
            site_id (int | str): The ID of the site.

        Returns:
            list: A list of typical-day objects, each carrying `id`,
                `label`, `isDefault` and `timeRangeConfigurations`.

        Raises:
            Exception: If an error occurs while retrieving the typical
                days.

        """

        return self._paginate(f"/typicaldays?siteId={site_id}")
