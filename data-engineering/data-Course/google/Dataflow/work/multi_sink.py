import apache_beam as beam

INPUT = "./sample_data/orders.csv"

def build(pipeline):
    return (
        pipeline
        | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        | "KeyByRegion" >> beam.Map(lambda line: (line.split(",")[3], 1))
        | "CountByRegion" >> beam.combiners.Count.PerKey()
    )

with beam.Pipeline() as p:
    summary = build(p)
    (summary | "FormatList" >> beam.Map(lambda kv: f"{kv[0]}={kv[1]}")
     | "WriteList" >> beam.io.WriteToText("./out/sink_list", num_shards=1, shard_name_template=""))
    (summary | "FormatCsv" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
     | "WriteCsv" >> beam.io.WriteToText("./out/sink_csv", num_shards=1, shard_name_template="", header="region,count"))
    (summary | "FormatJson" >> beam.Map(lambda kv: '{"region": "%s", "count": %d}' % (kv[0], kv[1]))
     | "WriteJson" >> beam.io.WriteToText("./out/sink_json", num_shards=1, shard_name_template=""))
