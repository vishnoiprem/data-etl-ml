import apache_beam as beam
from apache_beam.io import parquetio
import pyarrow as pa

SCHEMA = pa.schema([
    pa.field("order_id", pa.string()),
    pa.field("region", pa.string()),
    pa.field("amount", pa.float64()),
])

with beam.Pipeline() as p:
    rows = (
        p
        | "C" >> beam.Create([{"order_id": "o1", "region": "EMEA", "amount": 10.5}])
    )
    rows | "W" >> parquetio.WriteToParquet("./out/probe_pq", schema=SCHEMA, num_shards=1, file_name_suffix=".parquet")
print("OK")
