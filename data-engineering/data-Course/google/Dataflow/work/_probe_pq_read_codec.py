import apache_beam as beam
from apache_beam.io import parquetio
import pyarrow as pa
SCHEMA = pa.schema([pa.field("order_id", pa.string())])
with beam.Pipeline() as p:
    rows = p | "C" >> beam.Create([{"order_id":"o1"}])
    rows | "W" >> parquetio.WriteToParquet("./out/c3_pq_snappy", schema=SCHEMA, num_shards=1, codec="snappy", file_name_suffix=".parquet")
with beam.Pipeline() as p:
    rows = p | "R" >> parquetio.ReadFromParquet("./out/c3_pq_snappy-*.parquet")
    print("read ok", rows.element_type)
