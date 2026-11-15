"""Execute the user's Beam notebooks locally, and record what they print.

The notebooks in ``Lab-sessions-beam-dataflow/`` were written against Cloud
Storage and BigQuery.  This runner executes each code cell on the Direct
Runner, with the cloud paths rewritten to the local sample data, so the
material's claimed outputs can be checked rather than believed.

A notebook's cells share one namespace, so the runner accumulates the
successful cells' source and replays them together — that is what makes
``BUCKET_NAME`` defined in cell 45 visible in cell 49.

Cells that need a live GCP project (BigQuery, Pub/Sub, Dataflow job
submission) are skipped and reported as ``SKIPPED`` rather than failed.

Run it directly::

    python _run_notebooks.py              # all notebooks
    python _run_notebooks.py Beam        # one notebook, by name
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import textwrap

HERE = pathlib.Path(__file__).resolve().parent
COURSE = HERE.parent.parent
REPO = COURSE.parent.parent.parent

sys.path.insert(0, str(HERE))

from beam_paths import LAB_DIR, OUT_ROOT, SAMPLE_DATA, rewrite  # noqa: E402

# Cells whose code needs a live GCP project.  Matched on a marker string.
SKIP_MARKERS = (
    "ReadFromBigQuery",
    "WriteToBigQuery",
    "ReadFromPubSub",
    "google.cloud.logging",
    "pubsub_v1",
    # The two "pipeline creation" cells are sketches: they read from the
    # placeholder path "path", which does not exist anywhere.
    "beam.io.Read(",
    "beam.io.Write(",
)

NOTEBOOKS = [
    "Beam.ipynb",
    "usecase1.ipynb",
    "Usecase2.ipynb",
    "Windowing.ipynb",
    "Streaming Pipeline/Streami-Pipeline.ipynb",
]

# A cell that is a Jupyter shell escape rather than Python.
MAGIC = re.compile(r"^\s*!|^\s*%")

# The pre-run preamble: beam imported, and a Direct Runner option set that
# every pipeline in the material can pick up.
PREAMBLE = textwrap.dedent(
    """
    import apache_beam as beam
    from apache_beam.options.pipeline_options import PipelineOptions
    from pathlib import Path as _Path

    _SAMPLE_ROOT = str(
        _Path(
            "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google"
            "/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice"
            "/Lab-sessions-beam-dataflow/sample_data"
        )
    )
    _OUT_ROOT = str(
        _Path(
            "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google"
            "/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice/beam"
            "/_notebook_run/_out"
        )
    )
    _Path(_OUT_ROOT).mkdir(parents=True, exist_ok=True)

    # The material builds bucket paths from this variable.
    BUCKET_NAME = _SAMPLE_ROOT

    _opts = PipelineOptions([
        "--runner=DirectRunner",
        "--environment_type=LOOPBACK",
    ])
    beam_opts = _opts
    opts = _opts
    beam_options = _opts
    """
)


def find_interpreter() -> str | None:
    for candidate in [
        REPO / ".env" / "bin" / "python",
        COURSE / "practice" / ".beam-venv" / "bin" / "python",
    ]:
        if not candidate.exists():
            continue
        probe = subprocess.run(
            [str(candidate), "-c", "import apache_beam"],
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return str(candidate)
    return None


def code_cells(nb_path: pathlib.Path) -> list[tuple[int, str]]:
    """Return (index, source) for each code cell in a notebook."""
    nb = json.loads(nb_path.read_text())
    out = []
    for i, cell in enumerate(nb.get("cells", []), start=1):
        if cell.get("cell_type") == "code":
            out.append((i, "".join(cell.get("source", []))))
    return out


def should_skip(source: str) -> str | None:
    """Return the reason a cell cannot run locally, or None.

    A cell that asks for the Dataflow runner is *not* skipped: the runner is
    swapped for the Direct Runner, so the pipeline logic still executes.
    """
    for marker in SKIP_MARKERS:
        if marker in source:
            return marker
    return None


def is_magic(source: str) -> bool:
    """True if the cell is a Jupyter shell escape, not Python."""
    return any(MAGIC.match(line) for line in source.splitlines() if line.strip())


def prepare(source: str) -> str:
    """Rewrite a cell so it runs locally.

    - ``gs://`` paths become local sample-data paths.
    - A bare relative filename that exists in the sample data becomes an
      absolute local path.
    - ``beam.Pipeline()`` gets the Direct Runner options.
    - The Dataflow runner is swapped for the Direct Runner.
    """
    source = rewrite(source)
    source = _resolve_relative(source)
    source = source.replace("beam.Pipeline()", "beam.Pipeline(options=beam_opts)")
    # A cell that asks for the Dataflow runner runs locally instead.  The
    # Dataflow job cannot be submitted here, but the pipeline logic can.
    source = source.replace("'DataflowRunner'", "'DirectRunner'")
    source = source.replace('"DataflowRunner"', '"DirectRunner"')
    return source


# A quoted bare filename, e.g. "sales_data.csv".
BARE_FILE = re.compile(r'"(?P<name>[A-Za-z0-9_][A-Za-z0-9_.-]*\.(?:csv|txt|json|avro|parquet))"')

# The files the sample data folder actually holds.
SAMPLE_FILES = {
    "sales_data.csv",
    "transactions.csv",
    "employees.csv",
    "users.txt",
    "orders.txt",
    "products.txt",
    "user_events.csv",
    "user_data.csv",
    "sales.csv",
}


def _resolve_relative(source: str) -> str:
    """Point a bare sample filename at the sample data folder."""
    def replace(match: re.Match) -> str:
        name = match.group("name")
        if name not in SAMPLE_FILES:
            return match.group(0)
        return '"' + str(SAMPLE_DATA / name) + '"'

    return BARE_FILE.sub(replace, source)


def run_cells(
    interpreter: str, sources: list[str], cwd: pathlib.Path
) -> tuple[int, str, str]:
    """Run an accumulated list of cell sources as one script."""
    body = "\n\n".join(prepare(s) for s in sources)
    script = cwd / "_cell.py"
    script.write_text(PREAMBLE + "\n" + body)
    try:
        result = subprocess.run(
            [interpreter, str(script)],
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=300,
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        script.unlink(missing_ok=True)


def main() -> int:
    names = sys.argv[1:]
    interpreter = find_interpreter()
    if not interpreter:
        print("No interpreter with apache_beam found.", file=sys.stderr)
        return 2

    out_dir = HERE / "_notebook_run"
    out_dir.mkdir(exist_ok=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    for name in NOTEBOOKS:
        if names and not any(n.lower() in name.lower() for n in names):
            continue
        nb_path = LAB_DIR / name
        if not nb_path.exists():
            continue

        slug = name.replace("/", "__").replace(".ipynb", "")
        report: list[str] = [f"NOTEBOOK {name}", "=" * 70]

        # Cells accumulate: a notebook's namespace is shared.
        accumulated: list[str] = []

        for index, source in code_cells(nb_path):
            if is_magic(source):
                report.append(f"\n--- cell {index} --- SKIPPED (jupyter magic)")
                continue

            reason = should_skip(source)
            if reason:
                report.append(f"\n--- cell {index} --- SKIPPED (needs {reason})")
                continue

            accumulated.append(source)
            code, stdout, stderr = run_cells(interpreter, accumulated, out_dir)

            report.append(f"\n--- cell {index} --- exit {code}")
            report.append(stdout.rstrip())
            if code != 0:
                report.append("STDERR:")
                report.append(stderr.strip()[-1200:])
                # The namespace is broken; drop back to the last good state.
                accumulated.pop()

        target = out_dir / f"{slug}.txt"
        target.write_text("\n".join(report))
        print(f"{name} -> {target}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
