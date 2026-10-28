import apache_beam as beam
from apache_beam.coders import coders
from apache_beam.coders.typecoders import registry


class Order:
    def __init__(self, order_id, region, amount):
        self.order_id = order_id
        self.region = region
        self.amount = amount

    def __repr__(self):
        return f"Order({self.order_id!r}, {self.region!r}, {self.amount!r})"


class OrderCoder(coders.Coder):
    def encode(self, order):
        return f"{order.order_id}|{order.region}|{order.amount:.2f}".encode("utf-8")

    def decode(self, encoded):
        order_id, region, amount = encoded.decode("utf-8").split("|")
        return Order(order_id, region, float(amount))


registry.register_coder(Order, OrderCoder())

print("registered coder:", type(registry.get_coder(Order)).__name__)
print("deterministic:", registry.get_coder(Order).is_deterministic())

with beam.Pipeline() as p:
    orders = (
        p
        | "Create" >> beam.Create([Order("o1", "EMEA", 10.5), Order("o2", "AMER", 3.25)])
        | "Annotate" >> beam.Map(lambda o: o)
    )
    print("element_type:", orders.element_type)
