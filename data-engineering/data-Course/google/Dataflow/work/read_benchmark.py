"""Time reading the same rows from each format."""

import statistics
import time

import apache_beam as beam
from apache_beam.io import parquetio

RUNS = 3


def time_read(make_reader) -> tuple[float, float]:
    """Return (best, median) read time over RUNS pipelines."""
    timings = []
    for run in range(RUNS):
        started = time.perf_counter()
        with beam.Pipeline() as p:
            rows = p | "Read" >> make_reader()
            keyed = rows | "Key" >> beam.Map(lambda row: (1, 1))
            counted = keyed | "Count" >> beam.combiners.Count.PerKey()
            counted | "Write" >> beam.io.WriteToText(
                f"out/bench_{run}", num_shards=1, shard_name_template=""
            )
        timings.append(time.perf_counter() - started)
    return min(timings), statistics.median(timings)


CASES = [
    ("csv     ", lambda: beam.io.ReadFromText("out/formats/csv")),
    ("ndjson  ", lambda: beam.io.ReadFromText("out/formats/ndjson")),
    ("parquet ", lambda: parquetio.ReadFromParquet("out/formats/parquet-*.parquet")),
]

for label, make_reader in CASES:
    best, median = time_read(make_reader)
    print(f"{label} best={best:.3f}s median={median:.3f}s")
