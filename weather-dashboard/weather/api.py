import requests
from dataclasses import dataclass
from typing import Optional

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


@dataclass
class Location:
    name: str
    country: str
    latitude: float
    longitude: float


@dataclass
class CurrentWeather:
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    condition: str
    location: Location


@dataclass
class DailyForecast:
    date: str
    temp_max: float
    temp_min: float
    precipitation: float
    condition: str


def geocode(city: str) -> Optional[Location]:
    resp = requests.get(GEOCODE_URL, params={"name": city, "count": 1, "language": "en"}, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        return None
    r = results[0]
    return Location(
        name=r["name"],
        country=r.get("country", ""),
        latitude=r["latitude"],
        longitude=r["longitude"],
    )


def fetch_weather(location: Location) -> tuple[CurrentWeather, list[DailyForecast]]:
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "forecast_days": 7,
        "timezone": "auto",
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    c = data["current"]
    current = CurrentWeather(
        temperature=c["temperature_2m"],
        feels_like=c["apparent_temperature"],
        humidity=c["relative_humidity_2m"],
        wind_speed=c["wind_speed_10m"],
        condition=WMO_CODES.get(c["weather_code"], "Unknown"),
        location=location,
    )

    daily_data = data["daily"]
    forecasts = [
        DailyForecast(
            date=daily_data["time"][i],
            temp_max=daily_data["temperature_2m_max"][i],
            temp_min=daily_data["temperature_2m_min"][i],
            precipitation=daily_data["precipitation_sum"][i],
            condition=WMO_CODES.get(daily_data["weather_code"][i], "Unknown"),
        )
        for i in range(len(daily_data["time"]))
    ]
    return current, forecasts
