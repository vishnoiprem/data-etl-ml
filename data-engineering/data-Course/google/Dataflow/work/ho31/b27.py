"""Demonstrate the ReadFromCsv schema-inference trap."""
import os

import apache_beam as beam

WORK = "./out/hands_on/drift"
os.makedirs(WORK, exist_ok=True)

V1 = os.path.join(WORK, "v1.csv")
V2 = os.path.join(WORK, "v2.csv")

with open(V1, "w", encoding="utf-8") as handle:
    handle.write("order_id,region,amount\no1,EMEA,10.5\no2,AMER,20.0\n")

with open(V2, "w", encoding="utf-8") as handle:
    handle.write(
        "order_id,region,amount,channel\no1,EMEA,10.5,web\no2,AMER,20.0,mobile\n"
    )


def read(path, label, **kwargs):
    """Read a CSV and print the inferred row type."""
    with beam.Pipeline() as pipeline:
        rows = (
            pipeline
            | "Read" >> beam.io.ReadFromCsv(path, **kwargs)
            | "Print" >> beam.Map(print)
        )
        print(f"--- {label} ---")


def main():
    read(V1, "v1: three columns, schema inferred")
    read(V2, "v2: four columns, schema inferred")

    # Now pin the schema to the *v1* shape and read the *v2* file.
    read(
        V2,
        "v2 read with the v1 schema pinned — the new column is dropped silently",
        dtype={"order_id": str, "region": str, "amount": float},
    )


if __name__ == "__main__":
    main()
