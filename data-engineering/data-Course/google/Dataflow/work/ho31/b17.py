from dataclasses import dataclass
from typing import Optional

from apache_beam.coders import typecoders


@dataclass
class Order:
    order_id: str
    region: str
    amount: float
    discount_code: Optional[str] = None


typecoders.registry.register_row(Order)
