"""Write the course's orders as CSV, NDJSON and Parquet, for comparison."""

import json
import shutil

import apache_beam as beam
import pyarrow as pa
from apache_beam.io import parquetio

FIELDS = [
    "order_id",
    "customer_id",
    "order_ts",
    "region",
    "channel",
    "currency",
    "status",
    "amount",
    "product_id",
]

PARQUET_SCHEMA = pa.schema(
    [
        pa.field("order_id", pa.string()),
        pa.field("customer_id", pa.string()),
        pa.field("order_ts", pa.string()),
        pa.field("region", pa.string()),
        pa.field("channel", pa.string()),
        pa.field("currency", pa.string()),
        pa.field("status", pa.string()),
        pa.field("amount", pa.float64()),
        pa.field("product_id", pa.string()),
    ]
)


def parse_order(line: str) -> dict:
    """Parse one CSV order line into a dict with a typed amount."""
    values = line.split(",")
    row = dict(zip(FIELDS, values))
    row["amount"] = float(row["amount"])
    return row


def to_csv(row: dict) -> str:
    """Render one order as a CSV line."""
    return ",".join(str(row[field]) for field in FIELDS)


def main() -> None:
    """Run the three writes."""
    for directory in ["out/formats/csv", "out/formats/ndjson", "out/formats/parquet"]:
        shutil.rmtree(directory, ignore_errors=True)

    with beam.Pipeline() as p:
        orders = (
            p
            | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
            | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
            | "Parse" >> beam.Map(parse_order)
        )

        orders | "ToCsv" >> beam.Map(to_csv) | "WriteCsv" >> beam.io.WriteToText(
            "out/formats/csv",
            num_shards=1,
            shard_name_template="",
            header=",".join(FIELDS),
        )

        orders | "ToJson" >> beam.Map(json.dumps) | "WriteJson" >> beam.io.WriteToText(
            "out/formats/ndjson",
            num_shards=1,
            shard_name_template="",
        )

        orders | "WriteParquet" >> parquetio.WriteToParquet(
            "out/formats/parquet",
            schema=PARQUET_SCHEMA,
            num_shards=1,
            codec="snappy",
            file_name_suffix=".parquet",
        )

    print("wrote out/formats/{csv,ndjson,parquet}")


if __name__ == "__main__":
    main()
