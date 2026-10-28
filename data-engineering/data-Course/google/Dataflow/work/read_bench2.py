"""Repeat the read benchmark and report the best of N runs."""
import time, statistics
import apache_beam as beam
from apache_beam.io import parquetio

def time_read(make_reader, runs=5):
    times = []
    for i in range(runs):
        t0 = time.perf_counter()
        with beam.Pipeline() as p:
            rows = p | "R" >> make_reader()
            _ = rows | "Key" >> beam.Map(lambda r: (1, 1))
            _ = _ | "Count" >> beam.combiners.Count.PerKey()
            _ = _ | "W" >> beam.io.WriteToText(f"out/bench_{i}", num_shards=1, shard_name_template="")
        times.append(time.perf_counter() - t0)
    return min(times), statistics.median(times)

CASES = [
    ("csv    ", lambda: beam.io.ReadFromText("out/fc2/csv")),
    ("ndjson ", lambda: beam.io.ReadFromText("out/fc2/ndjson")),
    ("parquet", lambda: parquetio.ReadFromParquet("out/fc2/pq_snappy-00000-of-00001.parquet")),
]
for label, make in CASES:
    best, med = time_read(make)
    print(f"{label} best={best:.3f}s median={med:.3f}s")
