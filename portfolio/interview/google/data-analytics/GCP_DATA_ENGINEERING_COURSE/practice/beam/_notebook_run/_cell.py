
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from pathlib import Path as _Path

_SAMPLE_ROOT = str(
    _Path(
        "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google"
        "/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice"
        "/Lab-sessions-beam-dataflow/sample_data"
    )
)
_OUT_ROOT = str(
    _Path(
        "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google"
        "/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice/beam"
        "/_notebook_run/_out"
    )
)
_Path(_OUT_ROOT).mkdir(parents=True, exist_ok=True)

# The material builds bucket paths from this variable.
BUCKET_NAME = _SAMPLE_ROOT

_opts = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])
beam_opts = _opts
opts = _opts
beam_options = _opts

import apache_beam as beam

from apache_beam.options.pipeline_options import PipelineOptions

beam_options = PipelineOptions(
    runner = "DirectRunner",
    project="",
    region="",
    job_name="",
    temp_location="",
    staging_location=""
)

data = [
        {'id': 1, 'name': 'Alice', 'score': 90},
        {'id': 2, 'name': 'Bob', 'score': 85},
        {'id': 3, 'name': 'Charlie', 'score': 88}
    ]

with beam.Pipeline(options=beam_opts) as pipeline:
    output = (
        pipeline
        | "read from hardcoded" >> beam.Create(data)
        | "print the data" >> beam.Map(print)
    )


TEXT_SOURCE_PATH = "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice/Lab-sessions-beam-dataflow/sample_data/products.txt"

with beam.Pipeline(options=beam_opts) as pipeline:
    result = (
        pipeline
        | "read from text" >> beam.io.ReadFromText(TEXT_SOURCE_PATH, skip_header_lines=1) # pc1
        | "print the data" >> beam.Map(print)
    )

CSV_SOURCE_PATH = "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice/Lab-sessions-beam-dataflow/sample_data/sales.csv"

with beam.Pipeline(options=beam_opts) as pipeline:
    result = (
        pipeline
        | "read from csv" >> beam.io.ReadFromText(CSV_SOURCE_PATH, skip_header_lines=1) # pc1
        | "print the data" >> beam.Map(print)
    )

JSON_SOURCE_PATH = "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice/Lab-sessions-beam-dataflow/sample_data/employee_data.json"

with beam.Pipeline(options=beam_opts) as pipeline:
    result = (
        pipeline
        | "read from json" >> beam.io.ReadFromText(JSON_SOURCE_PATH) # pc1
        | "print the data" >> beam.Map(print)
    )

PARQUET_SOURCE_PATH = "/Users/prem/PycharmProjects/data-etl-ml/portfolio/interview/google/data-analytics/GCP_DATA_ENGINEERING_COURSE/practice/Lab-sessions-beam-dataflow/sample_data/export_001.parquet"

with beam.Pipeline(options=beam_opts) as pipeline:
    result = (
        pipeline
        | "read from parquet" >> beam.io.ReadFromParquet(PARQUET_SOURCE_PATH)
        | "limit to 5 records" >> beam.combiners.Sample.FixedSizeGlobally(5)
        | "print the data" >> beam.Map(print)
    )