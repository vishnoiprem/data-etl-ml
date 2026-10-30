#!/usr/bin/env python3
"""
build_notebooks.py — generate the course's exploratory notebooks.

The notebooks are *checked in*, not generated at read time; this script
exists so they stay consistent and so the linter has a single definition
of what a notebook must contain.

Each notebook:

  * is a valid ``nbformat`` 4.5 document;
  * imports only from the course's pure core modules;
  * carries no stored outputs (a notebook with stale outputs is a
    liability — a reader runs it and gets different numbers);
  * has a markdown cell before the first code cell explaining what the
    notebook is for.

The notebooks are executed by ``resources/audit_course.py`` through
``nbclient`` when it is available, and are skipped otherwise.

Usage:
    python resources/build_notebooks.py
    python resources/build_notebooks.py --check
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = COURSE_ROOT / "notebooks"

try:
    import nbformat
    from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook
except ImportError:  # pragma: no cover - the linter degrades gracefully
    nbformat = None  # type: ignore[assignment]

#: The preamble every notebook starts with. It puts the course core on
#: the path so a reader can run the notebook from the course root with
#: no installation step.
PREAMBLE = '''import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project" / "core").exists():
    COURSE_ROOT = Path.cwd().parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))

SAMPLE_DIR = COURSE_ROOT / "sample_data"
'''

#: The opening markdown cell for each notebook, keyed by title.
INTRO_CELLS = {
    "Explore the event stream": (
        "# Explore the event stream\n"
        "\n"
        "The raw event stream is the input to every stage of the pipeline.\n"
        "Before writing a single line of transformation code, look at what\n"
        "actually arrives.\n"
        "\n"
        "This notebook is the equivalent of opening the Pub/Sub subscription in\n"
        "the console and reading the first hundred messages. In a real project\n"
        "you would do this against the live topic; here it runs against the\n"
        "deterministic sample dataset, so every number in the output is one the\n"
        "course asserts against.\n"
        "\n"
        "Run it with `jupyter lab notebooks/` from the course root."
    ),
    "Validate and route to the dead-letter path": (
        "# Validate and route to the dead-letter path\n"
        "\n"
        "A validator that returns `True`/`False` gives you a dead-letter queue\n"
        "full of rows and a metric that cannot be split by cause. A validator\n"
        "that returns a **reason code** gives you a metric label, a partition\n"
        "key and a routing decision.\n"
        "\n"
        "This notebook runs the malformed dataset through the validator and\n"
        "shows the complete failure taxonomy."
    ),
    "Price the architectures": (
        "# Price the architectures\n"
        "\n"
        "The same workload can be run four ways. They cost different amounts of\n"
        "money, and the ranking is not obvious from first principles — which is\n"
        "why it is worth computing.\n"
        "\n"
        "The point of this notebook is that **the comparison is a function of its\n"
        "inputs, not a fixed ranking of technologies.** Change how long the\n"
        "pipeline runs, or how much of the table the query reads, and the winner\n"
        "changes."
    ),
}

#: Each notebook: ``(slug, title, [(markdown, code), ...])``.
#:
#: The markdown and the code that follows it are paired, so the
#: interleaving cannot drift — which is exactly the bug an earlier
#: two-list layout allowed.
NOTEBOOK_SPECS: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "01-explore-the-event-stream",
        "Explore the event stream",
        [
            (
                "## 1. Load the raw rows\n"
                "\n"
                "The file is CSV, but the pipeline treats every row as a\n"
                "*message* — the same shape Pub/Sub hands you.",
                "from pipeline_logic import ingest_events\n"
                "\n"
                "lines = (SAMPLE_DIR / 'events.csv').read_text(encoding='utf-8').splitlines()\n"
                "print(f'raw lines: {len(lines)}')\n"
                "print(lines[0])\n"
                "print(lines[1])",
            ),
            (
                "## 2. Ingest and split\n"
                "\n"
                "`ingest_events` returns two lists: the rows that passed\n"
                "validation and the rows that were rejected with a reason code.\n"
                "The split is the whole point of a landing zone — bad data goes\n"
                "somewhere specific.",
                "accepted, rejected = ingest_events(lines)\n"
                "print(f'accepted: {len(accepted)}')\n"
                "print(f'rejected: {len(rejected)}')\n"
                "accepted[0]",
            ),
            (
                "## 3. What is in a row?\n"
                "\n"
                "One normalised row. Every field is flat and primitive, because a\n"
                "BigQuery table with nested fields costs more to scan and more to\n"
                "reason about.",
                "row = accepted[0]\n"
                "for key, value in row.items():\n"
                "    print(f'{key:<16} {value!r}')",
            ),
            (
                "## 4. The cardinality of each field\n"
                "\n"
                "Low-cardinality fields are candidates for clustering.\n"
                "High-cardinality fields are candidates for a bug. Run this before\n"
                "you design the table, not after.",
                "for field in ('region', 'channel', 'currency', 'event_type'):\n"
                "    values = {r[field] for r in accepted}\n"
                "    print(f'{field:<12} {len(values):>3} distinct  {sorted(values)}')",
            ),
            (
                "## 5. The event-time span\n"
                "\n"
                "The windowing path derives the bucket from the **event timestamp**,\n"
                "never from arrival time. So the event-time span is what determines\n"
                "how many windows exist.",
                "from pipeline_logic import event_time_bounds, hours_spanned\n"
                "\n"
                "earliest, latest = event_time_bounds(accepted)\n"
                "print('earliest:', earliest)\n"
                "print('latest:  ', latest)\n"
                "print('hours spanned:', hours_spanned(accepted))",
            ),
        ],
    ),
    (
        "02-validate-and-route-to-the-dead-letter-path",
        "Validate and route to the dead-letter path",
        [
            (
                "## 1. The malformed file\n"
                "\n"
                "Twelve rows, each one malformed in a different way. The file is\n"
                "deliberately exhaustive: every reason the validator can emit\n"
                "appears at least once, so the taxonomy is testable rather than a\n"
                "hope.",
                "from pipeline_logic import ingest_events, reject_counts\n"
                "\n"
                "malformed = (SAMPLE_DIR / 'malformed_events.csv').read_text(encoding='utf-8').splitlines()\n"
                "print(f'malformed lines: {len(malformed)}')\n"
                "for line in malformed:\n"
                "    print(line)",
            ),
            (
                "## 2. The rejection reasons\n"
                "\n"
                "Each row is rejected with a stable, low-cardinality code. This is\n"
                "what you group by when you build the metric.",
                "accepted, rejected = ingest_events(malformed)\n"
                "print(f'accepted: {len(accepted)}')\n"
                "for reason, count in sorted(reject_counts(rejected).items()):\n"
                "    print(f'{reason:<24} {count}')",
            ),
            (
                "## 3. The detail of each rejection\n"
                "\n"
                "A reason code on its own tells you *what* failed. The detail tells\n"
                "you *why* — and it is the only part you must not put in a metric\n"
                "label, because it is unbounded.",
                "for item in rejected:\n"
                "    print(item['reason'].ljust(24) + ' ' + item['detail'])",
            ),
            (
                "## 4. Why a reason code and not an exception\n"
                "\n"
                "If the validator raised, the first bad row would kill the batch.\n"
                "If it returned `False`, you would know *that* a row failed but not\n"
                "*why*. The reason code gives you all three: the row survives, the\n"
                "cause is recorded, and the metric is splittable.",
                "from pipeline_logic import validate_event\n"
                "\n"
                "sample = {\n"
                "    'event_id': 'e1',\n"
                "    'user_id': 'u1',\n"
                "    'event_ts': '2026-01-15T00:00:00+00:00',\n"
                "    'event_type': 'order',\n"
                "    'region': 'EMEA',\n"
                "    'channel': 'web',\n"
                "    'currency': 'EUR',\n"
                "    'amount': 10.0,\n"
                "}\n"
                "print(validate_event(sample))\n"
                "\n"
                "broken = dict(sample, region='MARS')\n"
                "print(validate_event(broken))",
            ),
        ],
    ),
    (
        "03-price-the-architectures",
        "Price the architectures",
        [
            (
                "## 1. The four options\n"
                "\n"
                "A streaming pipeline, a Spark cluster, a partitioned warehouse scan\n"
                "and an unpartitioned one — all doing the same logical work.",
                "from cost_model import compare_architectures, format_comparison\n"
                "\n"
                "options = compare_architectures(scanned_tb=1.0, partition_factor=0.01)\n"
                "print(format_comparison(options))",
            ),
            (
                "## 2. Why the two zero-cost rows are zero\n"
                "\n"
                "They are zero because `streaming_hours` defaults to `0`. The\n"
                "Dataflow and Dataproc lines are priced per **vCPU-hour**; no hours\n"
                "were requested, so nothing was billed.\n"
                "\n"
                "Never read a `$0.00` streaming row as *free*. Read it as *the hours\n"
                "were not counted*.",
                "options = compare_architectures(\n"
                "    scanned_tb=1.0, partition_factor=0.01, streaming_hours=24\n"
                ")\n"
                "print(format_comparison(options))",
            ),
            (
                "## 3. The partitioning multiplier\n"
                "\n"
                "A hundred-fold reduction from the table layout alone, with no change\n"
                "to the query. This is the single highest-return optimisation in the\n"
                "whole course.",
                "from cost_model import BIGQUERY_ONDEMAND_PER_TB\n"
                "\n"
                "full = BIGQUERY_ONDEMAND_PER_TB * 1.0\n"
                "pruned = BIGQUERY_ONDEMAND_PER_TB * 1.0 * 0.01\n"
                "print(f'full scan:    ${full:.4f}')\n"
                "print(f'pruned scan:  ${pruned:.4f}')\n"
                "print(f'ratio:        {full / pruned:.0f}x')",
            ),
            (
                "## 4. The demo project's monthly bill\n"
                "\n"
                "The simulation prices every service the demo project uses. Note\n"
                "that the continuously-running services dominate — which is the\n"
                "opposite of what people expect when they think *BigQuery is\n"
                "expensive*.",
                "from platform_sim import build_demo_project\n"
                "\n"
                "project = build_demo_project()\n"
                "costs = project.estimate_monthly_cost()\n"
                "total = 0.0\n"
                "for service, cost in sorted(costs.items(), key=lambda kv: -kv[1]):\n"
                "    print(f'{service:<24} ${cost:>10.4f}')\n"
                "    total += cost\n"
                "print('TOTAL'.ljust(24) + ' $' + format(total, '>10.4f'))",
            ),
        ],
    ),
]


def build_notebook(title: str, sections: list[tuple[str, str]]):
    """Build a notebook object.

    Args:
        title: The notebook title.
        sections: The ``(markdown, code)`` pairs, in order.

    Returns:
        The ``nbformat`` notebook.
    """
    nb = new_notebook()
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python", "version": "3.11"}

    nb.cells.append(new_markdown_cell(INTRO_CELLS[title]))
    nb.cells.append(
        new_markdown_cell(
            "## 0. Setup\n"
            "\n"
            "Put the course's pure core modules on the path. No installation\n"
            "and no cloud SDK — that is the whole point of the split."
        )
    )
    nb.cells.append(new_code_cell(PREAMBLE))
    for markdown, code in sections:
        nb.cells.append(new_markdown_cell(markdown))
        nb.cells.append(new_code_cell(code))

    return nb


def main(argv: list[str] | None = None) -> int:
    """Generate the notebooks.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the checked-in notebooks match the generated ones",
    )
    args = parser.parse_args(argv)

    if nbformat is None:
        print("nbformat is not installed — cannot build notebooks")
        return 1

    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    drifted: list[str] = []

    for slug, title, sections in NOTEBOOK_SPECS:
        nb = build_notebook(title, sections)
        path = NOTEBOOKS_DIR / f"{slug}.ipynb"

        if args.check:
            if not path.exists():
                drifted.append(f"{path.name}: missing")
                continue
            existing = nbformat.read(path, as_version=4)
            # Compare the sources, not the metadata — a trailing
            # whitespace change in a cell is not worth a rebuild.
            new_sources = [cell.source for cell in nb.cells]
            old_sources = [cell.source for cell in existing.cells]
            if new_sources != old_sources:
                drifted.append(f"{path.name}: sources differ")
            continue

        nbformat.write(nb, path)
        print(f"wrote {path.relative_to(COURSE_ROOT)}")

    if args.check:
        if drifted:
            print(f"{len(drifted)} notebook(s) differ from the generated form:")
            for message in drifted:
                print(f"  ! {message}")
            return 1
        print("All notebooks match the generated form.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
