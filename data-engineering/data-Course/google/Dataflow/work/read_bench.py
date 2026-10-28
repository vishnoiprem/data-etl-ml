"""Time reading the same 5000 rows from CSV, NDJSON and Parquet."""
import time
import apache_beam as beam
from apache_beam.io import parquetio

def time_read(label, reader):
    t0 = time.perf_counter()
    with beam.Pipeline() as p:
        rows = p | "R" >> reader
        _ = rows | "Key" >> beam.Map(lambda r: (1, 1))
        _ = _ | "Count" >> beam.combiners.Count.PerKey()
        _ = _ | "W" >> beam.io.WriteToText(f"out/bench_{label}", num_shards=1, shard_name_template="")
    return time.perf_counter() - t0

print("csv     ", round(time_read("csv", beam.io.ReadFromText("out/fc2/csv")), 3))
print("ndjson  ", round(time_read("ndjson", beam.io.ReadFromText("out/fc2/ndjson")), 3))
print("parquet ", round(time_read("parquet", parquetio.ReadFromParquet("out/fc2/pq_snappy-00000-of-00001.parquet")), 3))
