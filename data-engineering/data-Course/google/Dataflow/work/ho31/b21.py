"""Inspect the coders Beam picks for the course pipeline."""
import apache_beam as beam
from apache_beam.coders import registry

from transforms import ParseOrderFn

VALID_LINE = (
    "o1,c1,2026-01-15T10:00:00+00:00,EMEA,web,EUR,complete,100.00,p1"
)


def main():
    with beam.Pipeline() as pipeline:
        orders = (
            pipeline
            | "Create" >> beam.Create([VALID_LINE])
            | "Parse" >> beam.ParDo(ParseOrderFn())
        )
        print("element_type:", orders.element_type)

    print()
    print("registry lookups:")
    for python_type in (int, float, str, bytes, bool, dict, tuple):
        print(f"  {python_type.__name__:>6} -> {registry.get_coder(python_type)}")


if __name__ == "__main__":
    main()
