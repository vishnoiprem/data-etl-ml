import apache_beam as beam
from apache_beam.io import parquetio

with beam.Pipeline() as p:
    rrows = p | "R" >> parquetio.ReadFromParquet("./out/probe_pq-*.parquet", as_rows=True)
    print("as_rows element_type:", rrows.element_type)
    rrows | "W" >> beam.io.WriteToText("./out/probe_pq_rows", num_shards=1, shard_name_template="")
