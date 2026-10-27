from urllib.parse import parse_qs, urlparse

import pytest
import responses

from comwatt_client import ComwattAPIError, ComwattAuthError

WEATHER_URL = "https://energy.comwatt.com/weather/data/2.5/forecast/"


@responses.activate
def test_forecast_city_success(client):
    mock_forecast = {
        "cod": "200",
        "cnt": 1,
        "list": [{"dt": 1700000000, "main": {"temp": 12.3}}],
        "city": {"name": "Nantes", "country": "FR"},
    }
    responses.add(
        responses.GET,
        WEATHER_URL,
        json=mock_forecast,
        status=200,
    )

    result = client.weather.forecast(city="Nantes")

    assert result == mock_forecast
    request = responses.calls[0].request
    assert request.method == "GET"
    parsed = urlparse(request.url)
    assert parsed.path == "/weather/data/2.5/forecast/"
    qs = parse_qs(parsed.query)
    assert qs["q"] == ["Nantes,FR"]
    assert qs["units"] == ["metric"]
    assert qs["lang"] == ["fr"]
    assert "zip" not in qs


@responses.activate
def test_forecast_zip_success(client):
    mock_forecast = {
        "cod": "200",
        "cnt": 1,
        "list": [{"dt": 1700000000, "main": {"temp": 8.0}}],
        "city": {"name": "Bordeaux", "country": "FR"},
    }
    responses.add(
        responses.GET,
        WEATHER_URL,
        json=mock_forecast,
        status=200,
    )

    result = client.weather.forecast(zip="33000")

    assert result == mock_forecast
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["zip"] == ["33000,FR"]
    assert "q" not in qs

    result_from_int = client.weather.forecast(zip=33000)

    assert result_from_int == mock_forecast
    request_from_int = responses.calls[1].request
    parsed_from_int = urlparse(request_from_int.url)
    qs_from_int = parse_qs(parsed_from_int.query)
    assert qs_from_int["zip"] == ["33000,FR"]


@responses.activate
def test_forecast_custom_params(client):
    mock_forecast = {"cod": "200", "cnt": 1, "list": [], "city": {}}
    responses.add(
        responses.GET,
        WEATHER_URL,
        json=mock_forecast,
        status=200,
    )

    result = client.weather.forecast(city="London", country="GB", units="imperial", lang="en")

    assert result == mock_forecast
    request = responses.calls[0].request
    parsed = urlparse(request.url)
    qs = parse_qs(parsed.query)
    assert qs["q"] == ["London,GB"]
    assert qs["units"] == ["imperial"]
    assert qs["lang"] == ["en"]


def test_forecast_city_and_zip_raises(client):
    with pytest.raises(ValueError):
        client.weather.forecast(city="Nantes", zip="33000")


def test_forecast_neither_raises(client):
    with pytest.raises(ValueError):
        client.weather.forecast()


@responses.activate
def test_forecast_unknown_city_error(client):
    responses.add(
        responses.GET,
        WEATHER_URL,
        json={"cod": "404", "message": "city not found"},
        status=404,
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.weather.forecast(city="Nowhereville")

    assert "404" in str(exc_info.value)


@responses.activate
def test_forecast_rate_limit_html_error(client):
    responses.add(
        responses.GET,
        WEATHER_URL,
        body="<html>Too Many Requests</html>",
        status=429,
        content_type="text/html",
    )

    with pytest.raises(ComwattAPIError) as exc_info:
        client.weather.forecast(city="Nantes")

    assert "429" in str(exc_info.value)


@responses.activate
def test_forecast_proxy_401_raises_auth_error(client):
    responses.add(
        responses.GET,
        WEATHER_URL,
        json={"detail": "unauthorized"},
        status=401,
    )

    with pytest.raises(ComwattAuthError) as exc_info:
        client.weather.forecast(city="Nantes")

    assert exc_info.value.status_code == 401
