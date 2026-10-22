from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class PlanningsMixin(_BaseClient):
    def get_plannings(self, site_id: int | str) -> list[dict[str, Any]]:
        """
        Retrieves the plannings (schedules) for the specified site.

        Auto-paginates: fetches every `?page=` and returns the concatenated
        `content` of all pages as a flat list. No trailing slash on the
        endpoint path (the slashed variant 404s). The server currently
        ignores `siteId` and returns the authenticated user's plannings,
        but the parameter is passed for forward compatibility.

        Args:
            site_id (int | str): The ID of the site.

        Returns:
            list: A list of planning objects, each carrying `id`, `device`,
                `isDefault`, `status` and `typicalDaySchedules`.

        Raises:
            Exception: If an error occurs while retrieving the plannings.

        """

        return self._paginate(f"/plannings?siteId={site_id}")
