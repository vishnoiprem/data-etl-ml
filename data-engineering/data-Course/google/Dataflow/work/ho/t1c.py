import shutil
import apache_beam as beam

INPUT = "./sample_data/orders.csv"

def run(name, before):
    out = f"./out/hands_on/shuffle_{name}"
    shutil.rmtree(out, ignore_errors=True)
    with beam.Pipeline() as p:
        lines = p | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        if before:
            kept = lines | "KeepComplete" >> beam.Filter(lambda l: ",complete," in l)
            keyed = kept | "KeyByRegion" >> beam.Map(lambda l: (l.split(",")[3], l))
        else:
            keyed = lines | "KeyByRegion" >> beam.Map(lambda l: (l.split(",")[3], l))
            kept = keyed | "KeepComplete" >> beam.Filter(lambda kv: ",complete," in kv[1])
        # count the elements that ENTER the keyed/shuffled stage
        keyed | "CountShuffleInput" >> beam.combiners.Count.Globally() | f"W{name}" >> beam.io.WriteToText(out, num_shards=1, shard_name_template="")
    print(name, open(out).read().strip())

run("filter_first", True)
run("filter_last", False)
