import apache_beam as beam

INPUT = "./sample_data/orders.csv"

def build(pipeline):
    parsed = (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "Parse" >> beam.Map(lambda line: line.split(","))
    )
    return parsed | "Reshuffle" >> beam.Reshuffle()

with beam.Pipeline() as p:
    parsed = build(p)
    (parsed | "TakeId" >> beam.Map(lambda parts: parts[0])
     | "WriteIds" >> beam.io.WriteToText("./out/order_ids", num_shards=1, shard_name_template=""))
    (parsed | "KeyByRegion" >> beam.Map(lambda parts: (parts[3], 1))
     | "CountByRegion" >> beam.combiners.Count.PerKey()
     | "FormatCounts" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
     | "WriteCounts" >> beam.io.WriteToText("./out/region_counts", num_shards=1, shard_name_template=""))
