import pytest
from unittest.mock import patch, MagicMock
from weather.api import geocode, fetch_weather, Location

MOCK_GEO = {
    "results": [{"name": "London", "country": "UK", "latitude": 51.5, "longitude": -0.12}]
}

MOCK_FORECAST = {
    "current": {
        "temperature_2m": 15.0,
        "apparent_temperature": 13.0,
        "relative_humidity_2m": 70,
        "wind_speed_10m": 20.0,
        "weather_code": 2,
    },
    "daily": {
        "time": ["2024-01-01", "2024-01-02"],
        "temperature_2m_max": [16.0, 14.0],
        "temperature_2m_min": [8.0, 7.0],
        "precipitation_sum": [0.0, 2.5],
        "weather_code": [0, 61],
    },
}


@patch("weather.api.requests.get")
def test_geocode_returns_location(mock_get):
    mock_get.return_value = MagicMock(json=lambda: MOCK_GEO)
    loc = geocode("London")
    assert loc.name == "London"
    assert loc.country == "UK"
    assert loc.latitude == 51.5


@patch("weather.api.requests.get")
def test_geocode_not_found(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {"results": []})
    assert geocode("xyznotacity") is None


@patch("weather.api.requests.get")
def test_fetch_weather_current(mock_get):
    mock_get.return_value = MagicMock(json=lambda: MOCK_FORECAST)
    loc = Location("London", "UK", 51.5, -0.12)
    current, _ = fetch_weather(loc)
    assert current.temperature == 15.0
    assert current.humidity == 70
    assert current.condition == "Partly cloudy"


@patch("weather.api.requests.get")
def test_fetch_weather_forecast(mock_get):
    mock_get.return_value = MagicMock(json=lambda: MOCK_FORECAST)
    loc = Location("London", "UK", 51.5, -0.12)
    _, forecasts = fetch_weather(loc)
    assert len(forecasts) == 2
    assert forecasts[0].condition == "Clear sky"
    assert forecasts[1].precipitation == 2.5
    assert forecasts[1].condition == "Slight rain"
