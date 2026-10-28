"""Write schema'd orders to Parquet and read them back."""
import shutil
from dataclasses import dataclass
from typing import Optional

import apache_beam as beam
import pyarrow as pa
from apache_beam.coders import typecoders

INPUT = "../../sample_data/orders.csv"
OUTPUT = "../../out/hands_on/orders_parquet"


@dataclass
class Order:
    """One order, with a schema Beam knows about."""

    order_id: str
    region: str
    amount: float
    discount_code: Optional[str] = None


typecoders.registry.register_row(Order)

# `WriteToParquet` wants a pyarrow schema.
ARROW_SCHEMA = pa.schema(
    [
        pa.field("order_id", pa.string()),
        pa.field("region", pa.string()),
        pa.field("amount", pa.float64()),
    ]
)


def parse_line(line):
    """Turn one CSV line into an Order."""
    parts = line.split(",")
    if len(parts) != 9:
        return None
    return Order(
        order_id=parts[0],
        region=parts[3],
        amount=float(parts[7]),
    )


def main():
    shutil.rmtree(OUTPUT, ignore_errors=True)

    with beam.Pipeline() as pipeline:
        (
            pipeline
            | "ReadOrders" >> beam.io.ReadFromText(INPUT)
            | "ParseOrders" >> beam.Map(parse_line)
            | "KeepValid" >> beam.Filter(lambda order: order is not None)
            | "WriteParquet" >> beam.io.WriteToParquet(
                OUTPUT,
                schema=ARROW_SCHEMA,
                num_shards=1,
            )
        )

    print("written")


if __name__ == "__main__":
    main()
