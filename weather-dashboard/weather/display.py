from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from weather.api import CurrentWeather, DailyForecast

console = Console()

CONDITION_ICONS: dict[str, str] = {
    "Clear sky": "☀️",
    "Mainly clear": "🌤️",
    "Partly cloudy": "⛅",
    "Overcast": "☁️",
    "Foggy": "🌫️",
    "Depositing rime fog": "🌫️",
    "Light drizzle": "🌦️",
    "Moderate drizzle": "🌧️",
    "Dense drizzle": "🌧️",
    "Slight rain": "🌧️",
    "Moderate rain": "🌧️",
    "Heavy rain": "⛈️",
    "Slight snow": "🌨️",
    "Moderate snow": "❄️",
    "Heavy snow": "❄️",
    "Slight showers": "🌦️",
    "Moderate showers": "🌧️",
    "Violent showers": "⛈️",
    "Thunderstorm": "⛈️",
    "Thunderstorm with hail": "⛈️",
    "Thunderstorm with heavy hail": "⛈️",
}


def _icon(condition: str) -> str:
    return CONDITION_ICONS.get(condition, "🌡️")


def show_current(weather: CurrentWeather) -> None:
    ic = _icon(weather.condition)
    content = (
        f"[bold]{ic} {weather.condition}[/bold]\n\n"
        f"[cyan]Temperature:[/cyan]  {weather.temperature}°C  "
        f"(feels like {weather.feels_like}°C)\n"
        f"[cyan]Humidity:[/cyan]     {weather.humidity}%\n"
        f"[cyan]Wind:[/cyan]         {weather.wind_speed} km/h"
    )
    console.print(Panel(
        content,
        title=f"[bold green]{weather.location.name}, {weather.location.country}[/bold green]",
        subtitle="Current conditions",
        border_style="blue",
        padding=(1, 2),
    ))


def show_forecast(forecasts: list[DailyForecast]) -> None:
    table = Table(title="7-Day Forecast", box=box.ROUNDED, border_style="blue", show_lines=True)
    table.add_column("Date", style="bold")
    table.add_column("Condition")
    table.add_column("High", justify="right", style="red")
    table.add_column("Low", justify="right", style="cyan")
    table.add_column("Rain", justify="right", style="blue")

    for f in forecasts:
        table.add_row(
            f.date,
            f"{_icon(f.condition)} {f.condition}",
            f"{f.temp_max}°C",
            f"{f.temp_min}°C",
            f"{f.precipitation} mm",
        )
    console.print(table)
