import time
import click
import psutil
from rich.live import Live
from monitor.collector import snapshot
from monitor.dashboard import build_layout, console


@click.command()
@click.option("--interval", "-i", default=2.0, type=float, help="Refresh interval in seconds")
def main(interval: float) -> None:
    """Real-time system resource monitor."""
    psutil.cpu_percent(interval=None)
    net = psutil.net_io_counters()
    prev_sent, prev_recv = net.bytes_sent, net.bytes_recv

    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            snap = snapshot(prev_sent, prev_recv)
            net_now = psutil.net_io_counters()
            prev_sent, prev_recv = net_now.bytes_sent, net_now.bytes_recv
            live.update(build_layout(snap))
            time.sleep(interval)


if __name__ == "__main__":
    main()
