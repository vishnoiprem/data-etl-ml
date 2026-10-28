from apache_beam.coders import coders


class OrderCoder(coders.Coder):
    """Encode an Order as a compact, deterministic byte string."""

    def encode(self, order):
        return f"{order.order_id}|{order.region}|{order.amount}".encode("utf-8")

    def decode(self, encoded):
        order_id, region, amount = encoded.decode("utf-8").split("|")
        return Order(order_id, region, float(amount))

    def to_type_hint(self):
        return Order

    def is_deterministic(self):
        return True


coders.registry.register_coder(Order, OrderCoder)
