"""Lab 1 — Beam basics.

Build your first Beam pipeline and see every stage of it execute.

The pipeline is deliberately tiny, because the point is not the data — it is
the *shape*:

    source  ->  PCollection  ->  transform  ->  PCollection  ->  sink

Everything else in this suite is that shape with more stages.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import apache_beam as beam

from beam_lib import banner, pipeline_options, read_output, show

OUT = "_out/basics"


def main() -> None:
    banner("Lab 1 — Beam basics")

    rows = [
        ("2026-01-15T00:00:00+00:00", "AMER", 10.0),
        ("2026-01-15T00:30:00+00:00", "AMER", 20.0),
        ("2026-01-15T01:00:00+00:00", "APAC", 30.0),
    ]

    options = pipeline_options()

    with beam.Pipeline(options=options) as pipeline:
        # ---- The source -------------------------------------------------
        # `beam.Create` makes a PCollection out of an in-memory iterable.
        # It is the stand-in for a real source (GCS, Pub/Sub, BigQuery).
        source = pipeline | "Create" >> beam.Create(rows)

        # ---- The transform ----------------------------------------------
        # `beam.Map` is a 1-to-1 transform: one input element, one output.
        # The `|` and `>>` operator label the step in the pipeline graph.
        mapped = source | "Map" >> beam.Map(lambda row: (row[1], row[2]))

        # ---- The sink ----------------------------------------------------
        # `WriteToText` writes one line per element to a shard file.
        _ = mapped | "Write" >> beam.io.WriteToText(OUT)

    banner("What the sink received")
    lines = read_output(f"{OUT}*")
    for line in lines:
        print(f"  {line}")

    banner("Stage 1 — the source")
    print(f"  Create produced {len(rows)} elements")
    print("  Each element is a tuple of (timestamp, region, amount)")

    banner("Stage 2 — the transform")
    print("  beam.Map applied a 1-to-1 function to every element")
    print(f"  {len(rows)} elements in -> {len(lines)} elements out")
    print("  Map never changes the element count. That is what makes it 1-to-1.")

    banner("Stage 3 — the sink")
    print(f"  WriteToText wrote {len(lines)} lines")
    print("  Beam names the file with a shard suffix: -00000-of-00001")
    print("  Your code never names the file. The runner does.")

    banner("The pipeline graph")
    print("  Create -> Map -> Write")
    print("  Three steps. The `|` operator feeds one PCollection into the next.")


if __name__ == "__main__":
    main()
