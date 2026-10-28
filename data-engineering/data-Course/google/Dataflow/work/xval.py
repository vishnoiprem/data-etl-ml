"""Cross-validate the pure-Python reference against the Beam pipeline."""
import sys
sys.path.insert(0, "project")
from transforms import build_revenue_summary, try_parse_order_line, is_valid_order

rows = []
with open("sample_data/orders.csv") as fh:
    for line in fh:
        r = try_parse_order_line(line)
        if r and is_valid_order(r):
            rows.append(r)

ref = build_revenue_summary(rows)
print("pure python:")
for k in sorted(ref):
    print(" ", k, ref[k])

import apache_beam as beam
from transforms import ParseOrderFn, RevenueByRegionFn

with beam.Pipeline() as p:
    parsed = (
        p
        | "Read" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "Parse" >> beam.ParDo(ParseOrderFn())
        | "Filter" >> beam.Filter(lambda o: o["status"] == "complete")
        | "Key" >> beam.Map(lambda o: (o["region"], o))
        | "Combine" >> beam.CombinePerKey(RevenueByRegionFn())
        | "Format" >> beam.Map(lambda kv: f"{kv[0]} {kv[1]['order_count']} {kv[1]['revenue_eur']}")
        | "Write" >> beam.io.WriteToText("out/xval", num_shards=1, shard_name_template="")
    )
