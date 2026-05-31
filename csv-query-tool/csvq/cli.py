import sys
import click
from csvq.analyzer import (
    load_csv, column_stats, filter_df,
    group_summary, detect_duplicates, correlation_matrix,
)
from csvq.report import console, print_overview, print_column_stats, print_dataframe, print_correlation


@click.group()
def cli():
    """Analyze CSV files from the terminal."""


@cli.command()
@click.argument("file")
@click.option("--delimiter", "-d", default=",", help="Column delimiter")
def info(file: str, delimiter: str) -> None:
    """Show overview and column statistics for FILE."""
    try:
        df = load_csv(file, delimiter)
    except FileNotFoundError:
        console.print(f"[red]File not found:[/red] {file}")
        sys.exit(1)
    print_overview(df, file)
    print_column_stats(column_stats(df))


@cli.command()
@click.argument("file")
@click.argument("query_expr")
@click.option("--delimiter", "-d", default=",")
@click.option("--output", "-o", default=None, help="Save result to CSV file")
def query(file: str, query_expr: str, delimiter: str, output: str) -> None:
    """Filter FILE rows using a pandas query expression.

    \b
    Examples:
      csvq query data.csv "age > 30"
      csvq query data.csv "region == 'West' and revenue > 5000"
    """
    df = load_csv(file, delimiter)
    result = filter_df(df, query_expr)
    print_dataframe(result, title=f"Query: {query_expr}")
    if output:
        result.to_csv(output, index=False)
        console.print(f"[green]Saved {len(result)} rows to {output}[/green]")


@cli.command()
@click.argument("file")
@click.argument("group_col")
@click.argument("agg_col")
@click.option("--func", "-f", default="sum", help="Aggregation: sum, mean, count, max, min")
@click.option("--delimiter", "-d", default=",")
def group(file: str, group_col: str, agg_col: str, func: str, delimiter: str) -> None:
    """Group FILE by GROUP_COL and aggregate AGG_COL."""
    df = load_csv(file, delimiter)
    try:
        result = group_summary(df, group_col, agg_col, func)
    except (KeyError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    print_dataframe(result, title=f"{func}({agg_col}) grouped by {group_col}")


@cli.command()
@click.argument("file")
@click.option("--delimiter", "-d", default=",")
def duplicates(file: str, delimiter: str) -> None:
    """Find duplicate rows in FILE."""
    df = load_csv(file, delimiter)
    dups = detect_duplicates(df)
    if dups.empty:
        console.print("[green]No duplicate rows found.[/green]")
    else:
        console.print(f"[yellow]Found {len(dups)} duplicate rows.[/yellow]")
        print_dataframe(dups, title="Duplicates")


@cli.command()
@click.argument("file")
@click.option("--delimiter", "-d", default=",")
def correlate(file: str, delimiter: str) -> None:
    """Show correlation matrix for numeric columns in FILE."""
    df = load_csv(file, delimiter)
    try:
        corr = correlation_matrix(df)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    print_correlation(corr)


if __name__ == "__main__":
    cli()
