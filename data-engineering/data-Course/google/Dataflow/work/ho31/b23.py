"""Define a Beam schema, register it, and write Parquet."""
from dataclasses import dataclass
from typing import Optional

from apache_beam.coders import typecoders
from apache_beam.typehints.schemas import typing_to_runner_api


@dataclass
class Order:
    """One order, with a schema Beam knows about."""

    order_id: str
    region: str
    amount: float
    discount_code: Optional[str] = None


def register():
    """Register the Order type and return its schema."""
    typecoders.registry.register_row(Order)
    return typing_to_runner_api(Order)


if __name__ == "__main__":
    schema = register()
    print(schema)
    coder = typecoders.registry.get_coder(Order)
    print()
    print("coder:", coder)
    print("deterministic:", coder.is_deterministic())
