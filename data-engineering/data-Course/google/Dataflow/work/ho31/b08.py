from dataclasses import dataclass

from apache_beam.coders import typecoders


@dataclass
class Order:
    order_id: str
    region: str
    amount: float


typecoders.registry.register_row(Order)
