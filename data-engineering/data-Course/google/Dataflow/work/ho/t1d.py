import shutil, sys
from pathlib import Path
sys.path.insert(0,'project')
import apache_beam as beam
from transforms import ParseOrderFn

INPUT = "./sample_data/orders.csv"

def run(name, before):
    out = f"./out/hands_on/shuffle_{name}"
    shutil.rmtree(out, ignore_errors=True)
    with beam.Pipeline() as p:
        lines = p | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())
        if before:
            kept = orders | "KeepComplete" >> beam.Filter(lambda o: o["status"] == "complete")
            keyed = kept | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
        else:
            keyed = orders | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
            kept = keyed | "KeepComplete" >> beam.Filter(lambda kv: kv[1]["status"] == "complete")
        keyed | "CountShuffleInput" >> beam.combiners.Count.Globally() | f"W{name}" >> beam.io.WriteToText(out, num_shards=1, shard_name_template="")
    print(name, open(out).read().strip())

run("filter_first", True)
run("filter_last", False)
