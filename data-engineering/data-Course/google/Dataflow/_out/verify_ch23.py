import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

from apache_beam.options.pipeline_options import (
    GoogleCloudOptions,
    PipelineOptions,
    StandardOptions,
)
from apache_beam.options import pipeline_options as po

for name in (
    "StandardOptions",
    "TypeOptions",
    "GoogleCloudOptions",
    "SetupOptions",
    "DirectOptions",
    "PrismRunnerOptions",
    "WorkerOptions",
    "PortableOptions",
    "StreamingOptions",
    "TestOptions",
):
    cls = getattr(po, name)
    print(f"{name:24} {cls.__mro__[1].__name__}")

print()
base = PipelineOptions([])
for name in (
    "StandardOptions",
    "TypeOptions",
    "GoogleCloudOptions",
    "SetupOptions",
    "DirectOptions",
):
    cls = getattr(po, name)
    print(f"{name:22} {len(base.view_as(cls)._visible_option_list()):3} options")

print()
options = PipelineOptions(
    ["--runner=BundleBasedDirectRunner", "--region=us-central1"]
)
for attribute in ("runner", "region", "project"):
    try:
        getattr(options, attribute)
        print(f"options.{attribute:10} -> OK")
    except AttributeError as exc:
        print(f"options.{attribute:10} -> {exc}")

print("standard.view runner:", options.view_as(StandardOptions).runner)
print("gcp.view region     :", options.view_as(GoogleCloudOptions).region)

print()
o2 = PipelineOptions(["--region=us-central1"])
g = o2.view_as(GoogleCloudOptions)
g.region = "europe-west1"
print("merged store    :", o2.get_all_options()["region"])
print("fresh view      :", o2.view_as(GoogleCloudOptions).region)
try:
    o2.region
except AttributeError:
    print("base still blind: AttributeError")

print()
all_options = PipelineOptions(["--runner=BundleBasedDirectRunner"]).get_all_options()
print("total options:", len(all_options))
for name in (
    "runner",
    "streaming",
    "project",
    "region",
    "job_name",
    "staging_location",
    "temp_location",
    "service_account_email",
    "requirements_file",
    "save_main_session",
    "experiments",
    "direct_num_workers",
    "direct_running_mode",
):
    print(f"  {name:22} {all_options.get(name)!r}")

try:
    PipelineOptions.get_all_options()
except TypeError as exc:
    print("TypeError:", exc)
try:
    PipelineOptions(["--runner=X"]).get_all_options(current_only=True)["runner"]
except KeyError as exc:
    print("KeyError:", exc)
