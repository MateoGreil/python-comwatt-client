from __future__ import annotations

from typing import Any

from ._core import _BaseClient

_WEATHER_FORECAST_URL = "https://energy.comwatt.com/weather/data/2.5/forecast/"


class WeatherProxy:
    """Namespaced access to the same-origin third-party weather proxy (outside `/api`)."""

    def __init__(self, client: _BaseClient) -> None:
        self._client = client

    def forecast(self, *, city: str | None = None, zip: str | int | None = None,
                 country: str = "FR", units: str = "metric", lang: str = "fr") -> dict[str, Any]:
        """
        Retrieves the OpenWeatherMap 5-day/3-hour forecast through the
        unauthenticated same-origin weather proxy.

        Exactly one of `city` or `zip` must be provided.

        Args:
            city (str): The city name to forecast (default: None).
            zip (str | int): The postal/zip code to forecast (default: None).
            country (str): The ISO 3166 country code (default: "FR").
            units (str): The unit system, e.g. "metric" or "imperial" (default: "metric").
            lang (str): The language code for the response text (default: "fr").

        Returns:
            dict: The raw OpenWeatherMap forecast payload.

        Raises:
            ValueError: If neither or both of `city` and `zip` are provided.
            ComwattAPIError: If the proxy or OpenWeatherMap rejects the request,
                e.g. HTTP 404 "city not found" when `city` or `zip` does not
                resolve to a known location. The request itself needs no
                authentication, but a 401 from the proxy surfaces as
                `ComwattAuthError` through the client's shared error mapping.

        """
        if (city is None) == (zip is None):
            raise ValueError("Exactly one of 'city' or 'zip' must be provided.")

        if city is not None:
            params = {"q": f"{city},{country}"}
        else:
            params = {"zip": f"{zip},{country}"}
        params["units"] = units
        params["lang"] = lang

        return self._client._request("GET", _WEATHER_FORECAST_URL, params=params).json()
