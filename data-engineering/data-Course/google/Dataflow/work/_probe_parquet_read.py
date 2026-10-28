import apache_beam as beam
from apache_beam.io import parquetio

with beam.Pipeline() as p:
    rows = p | "R" >> parquetio.ReadFromParquet("./out/probe_pq*")
    print("element_type:", rows.element_type)
    rows | "W" >> beam.io.WriteToText("./out/probe_pq_read", num_shards=1, shard_name_template="")

with beam.Pipeline() as p:
    rrows = p | "R2" >> parquetio.ReadFromParquet("./out/probe_pq*", as_rows=True)
    print("as_rows element_type:", rrows.element_type)
