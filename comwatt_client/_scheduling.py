from __future__ import annotations

from typing import Any

from ._core import _BaseClient


class SchedulingMixin(_BaseClient):
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

    def update_planning(self, planning_id: int | str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Updates a specific planning with the provided payload.

        Sends `payload` as-is as the request body to
        `PUT /plannings/{planning_id}`. Three pitfalls are known
        second-hand (from solareco's PlanningDto, not live-tested):

        1. An inline `device` object carrying the fastjson discriminator
           `"@class": "Device"` plus a numeric `id` is required — without
           the discriminator the API returns `400 "Failed to read request"`.
        2. Each schedule's `typicalDay` must be a full inline object; an
           id-only reference returns 500.
        3. The PUT replaces `typicalDaySchedules` wholesale — any user
           schedule omitted from the payload is deleted. Include every
           surviving schedule and re-read (e.g. via `get_plannings`)
           after writing. Schedules with `optimalPlanning: true` are
           server-managed and not writable.

        Args:
            planning_id (int | str): The ID of the planning.
            payload (dict): The payload to update the planning.

        Returns:
            dict: A dictionary containing the response from the API.

        Raises:
            Exception: If an error occurs while updating the planning.

        """
        return self._request("PUT", f"/plannings/{planning_id}", json=payload).json()

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

    def create_typical_day(self, site_id: int | str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Creates a new "typical day" template for the specified site.

        `siteId` is sent in the query string, not the request body —
        that placement is second-hand knowledge (from the solareco
        reverse-engineering) and was not live-tested. The payload is
        passed through unvalidated: build it from the objects returned
        by `get_typical_days` (each carrying `label`, `isDefault` and
        `timeRangeConfigurations` with `ON` / `OFF` / `COMWATT` modes,
        observed read-side). The response shape is not live-verified.

        Args:
            site_id (int | str): The ID of the site.
            payload (dict): The typical-day definition to create.

        Returns:
            dict: A dictionary containing the API response.

        Raises:
            Exception: If an error occurs while creating the typical
                day.

        """
        return self._request("POST", f"/typicaldays?siteId={site_id}", json=payload).json()

    def update_typical_day(self, typical_day_id: int | str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Updates an existing "typical day" template.

        The payload is passed through unvalidated: build it from the
        objects returned by `get_typical_days` (each carrying `label`,
        `isDefault` and `timeRangeConfigurations` with `ON` / `OFF` /
        `COMWATT` modes, observed read-side). The response shape is
        not live-verified.

        Args:
            typical_day_id (int | str): The ID of the typical day (the
                `id` field of a `get_typical_days` entry).
            payload (dict): The fields to update.

        Returns:
            dict: A dictionary containing the API response.

        Raises:
            Exception: If an error occurs while updating the typical
                day.

        """
        return self._request("PUT", f"/typicaldays/{typical_day_id}", json=payload).json()
