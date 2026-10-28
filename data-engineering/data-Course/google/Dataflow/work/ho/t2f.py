import sys
sys.path.insert(0, "./project")
import apache_beam as beam
from transforms import (ParseOrderFn, RevenueByRegionFn, format_summary_csv, to_summary_row)

with beam.Pipeline() as p:
    lines = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    keyed = orders | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
    kept = keyed | "KeepComplete" >> beam.Filter(lambda pair: pair[1]["status"] == "complete")
    summary = kept | "RevenueByRegion" >> beam.CombinePerKey(RevenueByRegionFn())
    (summary
     | "ToFlatRow" >> beam.Map(to_summary_row)
     | "FormatCsv" >> beam.Map(format_summary_csv)
     | "W" >> beam.io.WriteToText("./out/hands_on/x", num_shards=1, shard_name_template=""))
