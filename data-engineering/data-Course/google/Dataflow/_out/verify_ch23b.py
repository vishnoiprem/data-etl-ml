import sys
from pathlib import Path

sys.path.insert(0, str(Path("_out").resolve()))
sys.path.insert(0, str(Path("project").resolve()))

from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from course_options import CourseOptions

options = CourseOptions(
    ["--local_threshold=50.0", "--environment_name=staging", "--write_to_gcs"]
)

print("threshold  :", options.local_threshold)
print("environment:", options.environment_name)
print("to gcs     :", options.write_to_gcs)
print("describe   :", options.describe())
print("total options:", len(options.get_all_options()))

print()
standard = options.view_as(StandardOptions)
print("standard view runner:", standard.runner)
try:
    standard.local_threshold
except AttributeError as exc:
    print("standard.local_threshold ->", exc)

print()
# Precedence
o1 = PipelineOptions(["--region=us-east1"], region="us-west1")
print("kwargs beat flags:", o1.get_all_options()["region"])
o2 = PipelineOptions(["--region=us-east1"])
print("flag beats default:", o2.get_all_options()["region"])
o3 = PipelineOptions([])
print("default          :", o3.get_all_options()["region"])

print()
# The "discarded" hazard
o4 = PipelineOptions(["--input", "./sample_data/orders.csv"])
print("input survived:", "input" in o4.get_all_options())

print()
# _known_beam_flags
from beam_options import _known_beam_flags

argv = ["--input", "./sample_data/orders.csv", "--runner", "DirectRunner", "--verbose"]
print("before:", argv)
print("after :", _known_beam_flags(argv))
