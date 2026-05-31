import sys
import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
from search.indexer import InvertedIndex
from search.store import save, load

console = Console()
INDEX_FILE = "index.json"


def _index() -> InvertedIndex:
    if Path(INDEX_FILE).exists():
        return load(INDEX_FILE)
    return InvertedIndex()


@click.group()
def cli():
    """Mini full-text search engine."""


@cli.command()
@click.argument("title")
@click.argument("content")
def add(title: str, content: str) -> None:
    """Add a single document to the index."""
    idx = _index()
    doc_id = idx.add(title, content)
    save(idx, INDEX_FILE)
    console.print(f"[green]Added[/green] doc #{doc_id}: {title}  [dim]({len(idx)} total)[/dim]")


@cli.command(name="index")
@click.argument("file", type=click.Path(exists=True))
def index_file(file: str) -> None:
    """Bulk-index a JSON file containing [{\"title\": ..., \"content\": ...}, ...]."""
    docs = json.loads(Path(file).read_text())
    idx = _index()
    for doc in docs:
        idx.add(doc["title"], doc.get("content", ""))
    save(idx, INDEX_FILE)
    console.print(f"[green]Indexed {len(docs)} documents.[/green] Total in index: {len(idx)}")


@cli.command()
@click.argument("query")
@click.option("--top", "-n", default=5, help="Max results to show")
def search(query: str, top: int) -> None:
    """Search the index and show ranked results."""
    if not Path(INDEX_FILE).exists():
        console.print("[red]No index found.[/red] Use 'add' or 'index' first.")
        sys.exit(1)

    idx = load(INDEX_FILE)
    results = idx.search(query, top_k=top)

    if not results:
        console.print(f"[yellow]No results for:[/yellow] {query}")
        return

    table = Table(
        title=f'Results for "{query}" ({len(results)} found)',
        box=box.ROUNDED, border_style="blue",
    )
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Score", justify="right", width=7)
    table.add_column("Title", style="bold")
    table.add_column("Snippet")

    for rank, (score, doc) in enumerate(results, 1):
        snippet = doc.content[:90].replace("\n", " ")
        if len(doc.content) > 90:
            snippet += "..."
        table.add_row(str(rank), f"{score:.3f}", doc.title, snippet)

    console.print(table)


@cli.command()
def stats() -> None:
    """Show index statistics."""
    if not Path(INDEX_FILE).exists():
        console.print("[red]No index.[/red]")
        return
    idx = load(INDEX_FILE)
    console.print(f"Documents:    [bold]{len(idx)}[/bold]")
    console.print(f"Unique terms: [bold]{len(idx.index)}[/bold]")


@cli.command()
def clear() -> None:
    """Delete the index file."""
    if Path(INDEX_FILE).exists():
        Path(INDEX_FILE).unlink()
        console.print("[yellow]Index cleared.[/yellow]")
    else:
        console.print("No index to clear.")


if __name__ == "__main__":
    cli()
