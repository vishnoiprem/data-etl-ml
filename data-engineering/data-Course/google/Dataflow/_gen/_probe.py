import pathlib
import tempfile

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

o = PipelineOptions()
o.view_as(StandardOptions).runner = "BundleBasedDirectRunner"


def run_and_collect(build_steps, out_dir):
    with beam.Pipeline(options=o) as p:
        result = build_steps(p)
        _ = (result
             | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
             | "Write" >> beam.io.WriteToText(str(out_dir) + "/out", num_shards=1))


d = tempfile.mkdtemp()
run_and_collect(
    lambda p: (p
               | "Read" >> beam.Create([(1, 2)])
               | "Sum" >> beam.CombinePerKey(sum)),
    d,
)
for f in pathlib.Path(d).rglob("*"):
    if f.is_file():
        print(f.name, f.read_text())
