import click
from weather.api import geocode, fetch_weather
from weather.display import console, show_current, show_forecast


@click.command()
@click.argument("city")
@click.option("--forecast/--no-forecast", default=True, help="Show 7-day forecast")
def main(city: str, forecast: bool) -> None:
    """Show current weather and forecast for CITY."""
    with console.status(f"Fetching weather for [bold]{city}[/bold]..."):
        location = geocode(city)
        if not location:
            console.print(f"[red]City not found:[/red] {city}")
            raise SystemExit(1)
        current, forecasts = fetch_weather(location)

    show_current(current)
    if forecast:
        show_forecast(forecasts)


if __name__ == "__main__":
    main()
