import pathlib
import tempfile

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

o = PipelineOptions()
o.view_as(StandardOptions).runner = "BundleBasedDirectRunner"


def tag(item, tag_name):
    key, value = item
    return key, (tag_name, value)


events = [
    {"region": "AMER", "value": 10.0},
    {"region": "AMER", "value": 5.0},
    {"region": "APAC", "value": 20.0},
]


def inspect(item):
    return repr(item)


d = tempfile.mkdtemp()
with beam.Pipeline(options=o) as p:
    keyed = p | "Read" >> beam.Create(events) | "Key" >> beam.Map(
        lambda e: (e["region"], e["value"])
    )
    counts = keyed | "Count" >> beam.combiners.Count.PerKey()
    sums = keyed | "Sum" >> beam.CombinePerKey(sum)
    tc = counts | "TagCounts" >> beam.Map(lambda kv: tag(kv, "count"))
    ts = sums | "TagSums" >> beam.Map(lambda kv: tag(kv, "sum"))
    grouped = (tc, ts) | "GroupBoth" >> beam.CoGroupByKey()
    _ = grouped | "Inspect" >> beam.Map(inspect) | "Write" >> beam.io.WriteToText(
        str(d) + "/out", num_shards=1
    )

for f in pathlib.Path(d).rglob("*"):
    if f.is_file():
        print(f.read_text())
