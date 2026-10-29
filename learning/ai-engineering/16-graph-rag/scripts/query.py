"""Query the pipeline with a chosen strategy and print answer + citations."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from src.pipeline import STRATEGIES, GraphRAGPipeline


app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    question: str = typer.Argument(..., help="Question to ask"),
    strategy: str = typer.Option(
        "hybrid", "--strategy", "-s", help=f"One of {STRATEGIES}"
    ),
    rebuild: bool = typer.Option(False, help="Rebuild indices before answering"),
) -> None:
    if strategy not in STRATEGIES:
        raise typer.BadParameter(f"strategy must be one of {STRATEGIES}")

    pipeline = GraphRAGPipeline()
    if rebuild:
        from src.config import get_settings
        from src.ingestion import load_corpus
        from src.bm25_index import BM25Index
        from src.graph_builder import build_graph
        from src.vector_index import VectorIndex
        from src.pipeline import GraphRAGPipeline as _P

        s = get_settings()
        pipeline.chunks = load_corpus(s.sample_data_dir / "corpus")
        pipeline.vector_index.build(pipeline.chunks)
        pipeline.bm25_index.build(pipeline.chunks)
        pipeline.graph = build_graph(pipeline.chunks, pipeline.llm)
        pipeline._wire_retrievers()
    else:
        try:
            pipeline.load()
        except FileNotFoundError as e:
            console.print(f"[red]No persisted indices found[/red] ({e}).")
            console.print("Run [bold]make ingest[/bold] first, or pass --rebuild.")
            raise typer.Exit(code=1)

    result = pipeline.retrieve(question, strategy=strategy)
    answer = pipeline.generator.generate(result)

    console.rule(f"[bold]Answer ({strategy})[/bold]")
    console.print(Markdown(answer.text))
    console.rule("[bold]Citations[/bold]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Strategy")
    table.add_column("Doc")
    table.add_column("Chunk")
    table.add_column("Score")
    for cite, hit in zip(answer.citations, result.hits):
        table.add_row(cite.source, cite.doc_id, cite.chunk_id, f"{hit.score:.3f}")
    console.print(table)

    if result.graph_edges:
        console.rule("[bold]Graph trace[/bold]")
        console.print(f"Seeds: {', '.join(result.graph_seeds) or '(none)'}")
        for s_, r, t in result.graph_edges:
            console.print(f"  {s_} --[{r}]--> {t}")

    console.rule("[bold]Per-strategy contributions[/bold]")
    for strat, ids in result.contributions.items():
        console.print(f"  {strat:>8}: {ids}")


if __name__ == "__main__":
    app()
