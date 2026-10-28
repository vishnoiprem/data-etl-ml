import shutil, sys
from pathlib import Path
import apache_beam as beam
sys.path.insert(0, "./project")
from transforms import (ParseOrderFn, RevenueByRegionFn, format_summary_csv, to_summary_row)

INPUT = "./sample_data/orders.csv"

def count_elements(pipeline, *, filter_before_keying):
    lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    if filter_before_keying:
        keyed = (orders
            | "KeepComplete" >> beam.Filter(lambda o: o["status"] == "complete")
            | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o)))
    else:
        keyed = orders | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
        keyed | "KeepComplete" >> beam.Filter(lambda kv: kv[1]["status"] == "complete")
    total = keyed | "CountElements" >> beam.combiners.Count.Globally()
    return total

for name, before in (("filter-first", True), ("filter-last", False)):
    out = f"./out/hands_on/shuffle_{name}"
    shutil.rmtree(out, ignore_errors=True)
    with beam.Pipeline() as pipeline:
        counted = count_elements(pipeline, filter_before_keying=before)
        (counted | f"Write{name}" >> beam.io.WriteToText(out, num_shards=1, shard_name_template=""))
    print(f"{name}: {open(out).read().strip()} elements enter the shuffle")
