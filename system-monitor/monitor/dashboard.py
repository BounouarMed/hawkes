from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns
from rich import box
from monitor.collector import SystemSnapshot

console = Console()


def _bar(percent: float, width: int = 20) -> str:
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    if percent >= 90:
        return f"[red]{bar}[/red]"
    elif percent >= 70:
        return f"[yellow]{bar}[/yellow]"
    return f"[green]{bar}[/green]"


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n //= 1024
    return f"{n} PB"


def build_layout(snap: SystemSnapshot) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["header"].update(Panel(
        f"[bold cyan]System Monitor[/bold cyan]  —  {snap.timestamp.strftime('%Y-%m-%d  %H:%M:%S')}",
        border_style="cyan",
    ))

    cores_text = "  ".join(
        f"[dim]C{i}:[/dim] {_bar(p, 8)} {p:5.1f}%"
        for i, p in enumerate(snap.cpu_per_core)
    )
    cpu_panel = Panel(
        f"Total  {_bar(snap.cpu_percent)} [bold]{snap.cpu_percent:.1f}%[/bold]\n\n{cores_text}",
        title="[bold]CPU[/bold]",
        border_style="blue",
    )

    mem_panel = Panel(
        f"RAM   {_bar(snap.memory_percent)} {snap.memory_percent:.1f}%\n"
        f"      {_human(snap.memory_used)} / {_human(snap.memory_total)}\n\n"
        f"Swap  {_bar(snap.swap_percent)} {snap.swap_percent:.1f}%",
        title="[bold]Memory[/bold]",
        border_style="blue",
    )

    net_panel = Panel(
        f"[green]↑ Sent:[/green]  {_human(snap.net_bytes_sent)}/s\n"
        f"[cyan]↓ Recv:[/cyan]  {_human(snap.net_bytes_recv)}/s",
        title="[bold]Network[/bold]",
        border_style="blue",
    )

    layout["left"].update(Columns([cpu_panel, mem_panel, net_panel], equal=False))

    disk_table = Table(title="Disk", box=box.SIMPLE_HEAVY, border_style="blue")
    disk_table.add_column("Mount")
    disk_table.add_column("Used", justify="right")
    disk_table.add_column("Total", justify="right")
    disk_table.add_column("Usage")
    for mount, (used, total, pct) in list(snap.disk_usage.items())[:6]:
        disk_table.add_row(mount, _human(used), _human(total), f"{_bar(pct, 12)} {pct:.0f}%")

    proc_table = Table(title="Top Processes", box=box.SIMPLE_HEAVY, border_style="magenta")
    proc_table.add_column("Process", style="bold")
    proc_table.add_column("CPU %", justify="right")
    proc_table.add_column("MEM %", justify="right")
    for name, cpu, mem in snap.top_processes:
        proc_table.add_row(name[:28], f"{cpu:.1f}", f"{mem:.1f}")

    layout["right"].split_column(Layout(disk_table), Layout(proc_table))
    layout["footer"].update(Panel("[dim]Press Ctrl+C to exit[/dim]", border_style="dim"))
    return layout
