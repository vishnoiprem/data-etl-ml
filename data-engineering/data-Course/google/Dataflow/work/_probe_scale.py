import apache_beam as beam
import sys
runner = sys.argv[1]
path = sys.argv[2]
with beam.Pipeline(runner=runner) as p:
    rows = p | "R" >> beam.io.ReadFromCsv(path)
    n = rows | "Map" >> beam.Map(lambda r: (r.region, 1))
    n = n | "Count" >> beam.combiners.Count.PerKey()
    _ = n | "W" >> beam.io.WriteToText("./out/probe_count", num_shards=1, shard_name_template="")
print("OK", runner, path)
