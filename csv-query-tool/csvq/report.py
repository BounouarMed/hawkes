from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import pandas as pd
from csvq.analyzer import ColumnStats

console = Console()


def print_overview(df: pd.DataFrame, path: str) -> None:
    info = (
        f"[cyan]File:[/cyan]    {path}\n"
        f"[cyan]Rows:[/cyan]    {len(df):,}\n"
        f"[cyan]Columns:[/cyan] {len(df.columns)}\n"
        f"[cyan]Memory:[/cyan]  {df.memory_usage(deep=True).sum() / 1024:.1f} KB"
    )
    console.print(Panel(info, title="[bold green]CSV Overview[/bold green]", border_style="green"))


def print_column_stats(stats: list[ColumnStats]) -> None:
    table = Table(title="Column Statistics", box=box.ROUNDED, border_style="blue", show_lines=True)
    table.add_column("Column", style="bold")
    table.add_column("Type")
    table.add_column("Non-null", justify="right")
    table.add_column("Nulls", justify="right", style="red")
    table.add_column("Unique", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Mean", justify="right")

    for s in stats:
        table.add_row(
            s.name,
            s.dtype,
            str(s.count),
            str(s.nulls) if s.nulls else "[green]0[/green]",
            str(s.unique),
            str(s.min) if s.min is not None else "-",
            str(s.max) if s.max is not None else "-",
            str(s.mean) if s.mean is not None else "-",
        )
    console.print(table)


def print_dataframe(df: pd.DataFrame, title: str = "Results", max_rows: int = 50) -> None:
    if df.empty:
        console.print("[yellow]No rows match.[/yellow]")
        return
    table = Table(title=f"{title} ({len(df)} rows)", box=box.SIMPLE_HEAVY, border_style="blue")
    for col in df.columns:
        table.add_column(str(col))
    for _, row in df.head(max_rows).iterrows():
        table.add_row(*[str(v) for v in row])
    if len(df) > max_rows:
        console.print(f"[dim]... and {len(df) - max_rows} more rows[/dim]")
    console.print(table)


def print_correlation(corr: pd.DataFrame) -> None:
    table = Table(title="Correlation Matrix", box=box.ROUNDED, border_style="magenta")
    table.add_column("")
    for col in corr.columns:
        table.add_column(col, justify="right")
    for idx, row in corr.iterrows():
        values = []
        for col in corr.columns:
            v = row[col]
            if col == idx:
                values.append(str(v))
            elif abs(v) > 0.7:
                values.append(f"[bold red]{v}[/bold red]")
            elif abs(v) > 0.4:
                values.append(f"[yellow]{v}[/yellow]")
            else:
                values.append(str(v))
        table.add_row(str(idx), *values)
    console.print(table)
