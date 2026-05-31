# Weather Dashboard

A beautiful terminal weather app powered by the [Open-Meteo API](https://open-meteo.com/) — no API key required.

## Features

- Current conditions: temperature, feels-like, humidity, wind speed
- 7-day forecast with daily highs, lows, and precipitation
- Rich terminal UI with colors, panels, and icons
- Automatic timezone detection
- Works for any city in the world

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Current weather + 7-day forecast
python -m weather.cli London

# Just current conditions
python -m weather.cli "New York" --no-forecast

# Any city in the world
python -m weather.cli Tokyo
python -m weather.cli Paris
python -m weather.cli "Sao Paulo"
```

## Example output

```
╭──────────────────────────────────╮
│        London, GB                │
│   Current conditions             │
│                                  │
│   ⛅ Partly cloudy               │
│                                  │
│   Temperature:  15°C (feels 13°C)│
│   Humidity:     70%              │
│   Wind:         20 km/h          │
╰──────────────────────────────────╯

╭───────────────────────────────────────────────────╮
│                  7-Day Forecast                   │
├────────────┬──────────────────┬──────┬─────┬──────┤
│ Date       │ Condition        │ High │ Low │ Rain │
│ 2024-01-01 │ ☀️  Clear sky    │ 16°C │  8°C│ 0 mm │
│ 2024-01-02 │ 🌧️  Moderate rain│ 14°C │  7°C│ 2.5mm│
╰────────────┴──────────────────┴──────┴─────┴──────╯
```

## Run tests

```bash
pytest tests/ -v
```

## Stack

- **Click** — CLI framework
- **Rich** — terminal UI (tables, panels, colors)
- **Open-Meteo** — free weather API, no key required
- **requests** — HTTP client
- **pytest** — unit tests with mocked API calls
