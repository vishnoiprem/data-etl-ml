import apache_beam as beam
from apache_beam import pvalue

class SplitByAmount(beam.DoFn):
    def process(self, order):
        if order["amount"] >= 500.0:
            yield pvalue.TaggedOutput("large", order)
        else:
            yield pvalue.TaggedOutput("small", order)

with beam.Pipeline() as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseOrders" >> beam.Map(lambda line: {"amount": float(line.split(",")[7])})
    )
    split = orders | "SplitByAmount" >> beam.ParDo(SplitByAmount()).with_outputs("large", "small")
    (split["large"] | "FormatLarge" >> beam.Map(lambda o: "large")
     | "WriteLarge" >> beam.io.WriteToText("./out/large_orders", num_shards=1, shard_name_template=""))
    (split["small"] | "FormatSmall" >> beam.Map(lambda o: "small")
     | "WriteSmall" >> beam.io.WriteToText("./out/small_orders", num_shards=1, shard_name_template=""))
