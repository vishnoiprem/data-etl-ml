import sys
sys.path.insert(0, "./project")
import apache_beam as beam
from transforms import ParseOrderFn, RevenueByRegionFn, format_summary_csv

with beam.Pipeline() as p:
    lines = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    kept = orders | "KeepComplete" >> beam.Filter(lambda o: o["status"] == "complete")
    keyed = kept | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
    summary = keyed | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
    summary | "FormatCsv" >> beam.Map(format_summary_csv) | "W" >> beam.io.WriteToText("./out/hands_on/x", num_shards=1, shard_name_template="")
