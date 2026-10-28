# 5.2 — Creating a Flex Template

> **Section 5 · Dataflow Templates & Deployment · Lecture 5.2 · 6:30**

## 🎯 What you will learn

- What a flex template actually is: a Python file in GCS, run by path
- `gcloud dataflow flex-template build` and every flag it accepts
- The difference between `build` and `run`, and when you need each
- `--template-file-gcs-path` vs `--template`
- The worker script rules: self-contained, and **never bundle apache-beam**
- `--py-files` and `--requirements-file-requirements` for extra dependencies
- `--metadata` for template descriptions
- `--parameters` and how to read them with `PipelineOptions`
- `save_main_session`, and why your template breaks without it
- The version-pinning problem, and how to pin the SDK

---

## 🧠 Concept

### What a flex template is, precisely

A flex template is **a single Python file uploaded to Cloud Storage that
Dataflow executes on the worker**. That is the whole thing. There is no
container image, no registry, no build step in the Docker sense.

This is the crucial mental correction, because the word "template" suggests
something packaged and immutable. It is not. A flex template is:

```text
gs://YOUR_BUCKET/templates/orders-etl.py
```

That file is the template. When you run it, Dataflow:

1. downloads the file,
2. starts a worker with the Beam SDK **already installed**,
3. copies the file onto the worker's filesystem,
4. executes it as `__main__`,
5. the script builds a Beam pipeline and the runner takes over.

The file is not compiled, not frozen, not versioned by Dataflow. It is
re-read **on every job launch**. Which means:

- Edit the file in GCS and the next job uses the new version, with no
  rebuild and no redeploy.
- Two jobs launched a minute apart can run *different code*, because the file
  changed in between.
- "Which version of the template produced this output?" is a question about
  the contents of a GCS object at a point in time — not about a tag or a
  registry entry.

The path is the identity of the template. `gs://bucket/templates/orders.py`
and `gs://bucket/templates/orders-v2.py` are two different templates.

### Build vs run

The CLI has two verbs that are easy to confuse.

| | `flex-template build` | `flex-template run` |
|---|---|---|
| What it does | copies your local file to a GCS path | launches a job from a GCS path |
| Creates a job? | no | yes |
| Costs money? | no | yes |
| Takes a local file? | yes (`--template-file`) | no |
| Takes a GCS path? | yes (`--template-file-gcs-path`) | yes (`--template`) |
| When you use it | once per version of the code | every time you run the job |

The naming is historical and mildly unfortunate: `build` does not build
anything. It stages the template file and writes a metadata sidecar.

```bash
# build — do this when you change the code
gcloud dataflow flex-template build orders-etl \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --template-file=./orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging

# run — do this every time you want results
gcloud dataflow flex-template run orders-etl \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --template=gs://YOUR_BUCKET/templates/orders-etl.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging \
  --parameters="input=gs://YOUR_BUCKET/orders.csv" \
  --wait=false
```

The **staging and temp locations are required by both**, even though `build`
does not run any of your code. The reason is that `build` writes a metadata
sidecar next to the template that records the staging and temp configuration
the template expects to be used with. This is a real operational constraint:
the staging location you used at build time is the one the run should use.

### `--template-file-gcs-path` vs `--template`

This is the single most common confusion in a first deployment.

| Flag | Command | Meaning |
|---|---|---|
| `--template-file` | `build` | the **local** path to the Python file you are uploading |
| `--template-file-gcs-path` | `build` | the **GCS** path where the uploaded file will live |
| `--template` | `run` | the **GCS** path of an already-uploaded template file |

In `build`, you give it a local file and a destination. In `run`, you give
it only the destination — the file is already there.

The GCS path in `--template-file-gcs-path` and `--template` must be the
same string. A mismatch produces a job that fails at startup with a
`FileNotFoundError` on the worker, not a CLI error.

```bash
# These two must agree
--template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py
--template=gs://YOUR_BUCKET/templates/orders-etl.py
```

### The flags of `flex-template build`

| Flag | Required | What it does |
|---|---|---|
| `--template-file` | yes | local path to the Python file to upload |
| `--template-file-gcs-path` | yes | GCS path to upload it to |
| `--project` | yes | the project that owns the bucket and the job |
| `--region` | yes | the region the job will run in |
| `--temp-location` | yes | GCS path for scratch space |
| `--staging-location` | yes | GCS path for staged metadata and checkpoints |
| `--metadata` | no | a description attached to the template |
| `--py-files` | no | extra `.py` files to ship to the worker |
| `--requirements-file-requirements` | no | extra pip requirements to install on the worker |
| `--service-account` | no | the service account that will own the staged objects |
| `--sdk-location` | no | a custom SDK to use instead of the service default |
| `--experiments` | no | Beam runner experiments to enable |
| `--additional-experiments` | no | more experiments (GA) |
| `--network` | no | VPC network for the workers |
| `--subnetwork` | no | subnetwork for the workers |
| `--machine-type` | no | default machine type recorded in the template metadata |
| `--max-workers` | no | default worker ceiling recorded in the metadata |
| `--service-account` | no | the identity used for staging operations |

The build-time flags that matter in practice are the ones that get
**recorded in the template metadata and reused as defaults at run time**:
`--machine-type`, `--max-workers`, `--min-workers`, `--service-account`,
`--network`/`--subnetwork`, and the autoscaling settings. If you set
`--machine-type=n1-standard-4` at build time, you do not have to repeat it
at run time — but you can override it.

### The worker script requirements

A flex template worker script is executed as `__main__` on a worker. The
rules are specific, and violating them produces failures that look like
mysterious environment problems.

**Rule 1: It must be self-contained, or use `--py-files`.**

The worker downloads only the files you told it about. If your template
does `from transforms import parse_order_line`, that import fails unless
`transforms.py` was shipped alongside it.

Two ways to fix it:

```bash
# Option A — ship the extra module
gcloud dataflow flex-template build orders-etl \
  --template-file=./orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --py-files=./transforms.py \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging
```

```bash
# Option B — put everything in one file
# Just concatenate the shared code into the template file itself.
```

For a template of any size, Option B is usually less painful than managing
a `--py-files` list, because the `--py-files` paths are relative to the
directory where you ran the `build` command. A CI job that runs `build` from
a different directory silently ships the wrong files — or no files.

**Rule 2: Do NOT bundle apache-beam.**

This is the rule people get wrong most often, and the failure is expensive.

The worker **already has the Beam SDK installed**, at the version the
Dataflow service provides. If your template also ships `apache_beam` — in a
wheel, a vendored directory, a zipapp, a `--py-files` entry — you have two
copies of the SDK on the worker, and only one of them is the one the runner
is driving. The symptoms are baffling:

```text
AttributeError: module 'apache_beam' has no attribute 'io'
```

```text
TypeError: cannot pickle '_io.BufferedReader' object
```

```text
ValueError: Expected a str, got <class 'apache_beam.internal.pipeline_api.pipeline_api_pb2.Pipeline'>.
The pickling of Pipeline objects is not supported.
```

All three are usually the same root cause: the worker's `sys.path` has your
bundled Beam ahead of the service's Beam, so the transforms you construct
come from a *different* `apache_beam` module than the one the runner
serialises with. Pickling across that boundary fails.

The same applies to `--requirements-file-requirements`. **Never put
`apache-beam` in that file.**

**Rule 3: `save_main_session=True` if you use `beam.DoFn` classes.**

This one deserves its own section, because it is the most common
template-specific failure.

### `save_main_session` — the DoFn pickling rule

Beam serialises your `DoFn` classes to the worker with `pickle` (or
`dill`). A class defined in `__main__` — which is what a template file is,
since it runs as `__main__` — cannot be unpickled on the worker unless
Python can find the class by name.

`save_main_session=True` tells Beam to serialise the *entire* `__main__`
module's contents along with the pipeline, so the worker can reconstruct
your classes.

Without it, the job fails at submission or at the first bundle:

```text
Can't pickle <class '__main__.ParseOrderFn'>: attribute lookup
ParseOrderFn on __main__ failed
```

```text
AttributeError: Can't get attribute 'ParseOrderFn' on <module '__main__'>
```

With `save_main_session=True`, the whole `__main__` module is serialised.
The trade-offs are real:

| | `save_main_session=False` (default) | `save_main_session=True` |
|---|---|---|
| Payload size | small (just the classes) | the entire `__main__` module |
| Needs `__main__` to be importable? | no | no — that is the point |
| Works with `DoFn` classes in `__main__`? | no | yes |
| Works with module-level globals? | no | yes |
| Slower submission | no | yes, slightly |

The rule of thumb: **if your template defines a `DoFn` class or uses a
module-level global that the `DoFn` depends on, set
`save_main_session=True`.** If the template is only lambdas and
module-level functions, leave it off.

Note that `save_main_session` is a *Python SDK* option, not a `gcloud`
flag. You set it in the options object:

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(sys.argv[1:] + ["--save_main_session=True"])
```

But wait — `sys.argv[1:]` in a flex template contains the `--parameters`
values, which Beam does not recognise as options. You need to filter them
out. That is what the next section is about.

### `--parameters` and reading them

`--parameters` is how you pass runtime configuration into a flex template
without changing the file. The format is a comma-separated list of
`key=value` pairs:

```bash
--parameters="input=gs://YOUR_BUCKET/orders.csv,output=gs://YOUR_BUCKET/summary,statuses=complete"
```

Dataflow parses this string and exposes each key as a **pipeline option**
with the given name. `input` becomes `options.input`, `output` becomes
`options.output`.

```python
import sys

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(sys.argv[1:])
print("input:   ", getattr(options, "input", None))
print("output:  ", getattr(options, "output", None))
print("statuses:", getattr(options, "statuses", None))
```

The important detail: **the `--parameters` flag itself is consumed by
Dataflow, but the individual keys are also passed through to the worker's
command line as `--key=value`.** So `PipelineOptions(sys.argv[1:])` sees
them, and it also sees the original `--parameters=...` string, which Beam
does not know and will warn about.

There are two ways to handle this.

**Option A — filter the argv before building the options.** This is what
the course's `beam_options.py` does with `_known_beam_flags`.

**Option B — declare your parameters as known options.** The cleanest
approach is to define a `PipelineOptions` subclass with your parameters as
typed attributes. Then Beam parses them properly, with defaults and type
coercion:

```python
from apache_beam.options.pipeline_options import PipelineOptions


class TemplateOptions(PipelineOptions):
    """Options for the orders flex template."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--input", default="")
        parser.add_argument("--output", default="")
        parser.add_argument("--statuses", default="complete")


options = TemplateOptions(sys.argv[1:])
print(options.input, options.output, options.statuses)
```

With this approach, `--parameters="input=...,output=..."` populates
`options.input` and `options.output` directly, with the declared defaults
if you forget to pass them.

### The value-provider distinction

There is a subtle but important point about *when* the parameter value is
read.

| Read at | Where | Use when |
|---|---|---|
| Python evaluation time | `options.input` as a plain string | the value is needed before the pipeline is built — output paths, table names |
| Pipeline execution time | `beam.pvalue.ValueProvider` | the value is only needed inside a transform, and you want the pipeline to start before the value is known |

In almost all flex templates you want evaluation-time reading. A
`ValueProvider` in a `WriteToBigQuery` table argument works, but it forces
the runner to defer the table resolution, and the failure mode when the
parameter is missing is a runtime error in the sink rather than a clear
"you forgot `--input`" message at startup.

### `--metadata`

`--metadata` attaches a human-readable description to the template. It
appears in `gcloud dataflow templates describe` and in the Dataflow
console. Use it to record the version, the owner, and the source commit:

```bash
gcloud dataflow flex-template build orders-etl \
  --template-file=./orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --metadata="version=1.4.0,owner=data-platform,source=git@abc1234" \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging
```

The value is a comma-separated `key=value` list. It is metadata for humans
and for `gcloud` — it does not affect execution, and the template file does
not read it at runtime. If you want the template to know its own version at
runtime, put it in the file or pass it as a `--parameters` entry.

### Extra dependencies: `--py-files` and `--requirements-file-requirements`

Two mechanisms, for two different kinds of dependency.

**`--py-files`** ships Python source. Use it for modules you wrote.

```bash
gcloud dataflow flex-template build orders-etl \
  --template-file=./orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --py-files=./transforms.py,./schemas.py \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging
```

Notes on `--py-files`:

- Paths are **relative to the current working directory** of the `build`
  command.
- The files are placed on the worker's `sys.path`, so `import transforms`
  works.
- A **directory** can be shipped, in which case its contents go on the path.
- Package directories must keep their `__init__.py` to be importable as
  packages.

**`--requirements-file-requirements`** installs pip packages on the worker.
Use it for third-party libraries.

The flag name is awkward — it is `--requirements-file` (a path to a
requirements file) followed by `--requirements` (the packages to install).
It is read as one flag because `gcloud` parses `--flag=file` and
`--flag file` identically.

```bash
# requirements-extra.txt contains:
#   google-cloud-bigquery==3.11.0
#   pandas==2.2.3
#   jsonschema==4.23.0

gcloud dataflow flex-template build orders-etl \
  --template-file=./orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --requirements-file-requirements=google-cloud-bigquery==3.11.0,pandas==2.2.3,jsonschema==4.23.0 \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging
```

The install happens **on the worker, at job start**. That means:

- it adds 30–120 seconds to every job's startup,
- it fails the job if a version cannot be resolved or built,
- **the versions you develop against are not necessarily the versions that
  get installed** if you use unpinned requirements.

Pin exact versions (`==`) for anything that matters. `pandas>=2.0` will
eventually install a pandas that breaks your code.

And again: **never put `apache-beam` in the requirements list.** The worker
already has it.

### The version-pinning problem

This is the single biggest source of "works locally, fails in production",
and it deserves to be stated without hedging.

> **The template runs with the SDK version the Dataflow service has, not the
> version you developed against.**

When you run a flex template, the worker is provisioned by Dataflow with
whatever Beam SDK version the service currently ships for that Python
version. If the service ships Beam 2.65.0 and you wrote and tested your code
against 2.77.0 locally, **your template runs on 2.65.0**.

The symptoms of a version mismatch are specific:

| Symptom | Likely cause |
|---|---|
| `AttributeError: module 'apache_beam' has no attribute 'X'` | a transform added after the service's SDK version |
| `TypeError: ... got an unexpected keyword argument 'Y'` | a parameter added in a later version |
| `ImportError: cannot import name 'Z'` | a module moved in a later version |
| Works locally, `ImportError` on the worker | a dependency you had installed but did not ship |
| A deprecation warning becomes an error | a warning that became fatal upstream |

How to find the version the service is using:

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(environment.sdkSupportStatus)'
```

and in the job's worker logs:

```bash
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID" \
  --project=YOUR_PROJECT_ID --limit=200 --format=json \
  | jq -r '.[] | select(.textPayload | test("apache-beam"; "i")) | .textPayload'
```

### How to pin the SDK version

There are three options, in order of preference.

**Option 1 — `--sdk-location`.** Point the worker at a specific SDK build
instead of the service default.

```bash
gcloud dataflow flex-template build orders-etl \
  --template-file=./orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --sdk-location=gs://YOUR_BUCKET/sdk/apache-beam-2.77.0 \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging
```

The SDK location is a GCS prefix containing the SDK distribution. You build
it once and reuse it for every template. This is the only way to get
**byte-for-byte identical** SDK behaviour between your laptop and the
worker.

**Option 2 — Develop against the service's version.** Check what the
service ships, then install that exact version locally:

```bash
# What the service has
gcloud dataflow flex-template build probe \
  --template-file=./probe.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/probe.py \
  --project=YOUR_PROJECT_ID --region=us-central1 \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging

# Match it locally
pip install "apache-beam[gcp]==2.65.0"
```

This is the pragmatic choice. It means your local environment changes when
the service changes, which is uncomfortable but at least it is *visible*.

**Option 3 — Constrain the code, not the SDK.** Write the template so it
works across the range of SDK versions you care about:

```python
import apache_beam as beam

# Feature-detect rather than assume a version.
_HAS_AS_ITER = hasattr(beam.pvalue, "AsIter")
```

This is the most robust in the long run and the least convenient right now.
Use it when you cannot control the deploy cadence.

**A fourth option that is not pinning, but often gets confused with it:**
pinning your *dependencies* (not Beam) via
`--requirements-file-requirements`. This fixes your third-party libraries
but does nothing about the Beam version.

---

## 🛠️ Hands-On: Build and Run a Flex Template

This hands-on builds a real flex template. The local parts need no GCP
account; the GCP parts are clearly marked.

### The template file

Create `templates/orders_etl.py`:

```python
"""A flex template that reads orders and writes a per-region summary."""
from __future__ import annotations

import sys

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


class TemplateOptions(PipelineOptions):
    """Runtime options for the orders flex template."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--input", default="")
        parser.add_argument("--output", default="")
        parser.add_argument("--statuses", default="complete")


def run(argv: list[str] | None = None) -> int:
    """Read the parameters, build the pipeline, run it."""
    args = list(argv if argv is not None else sys.argv[1:])
    options = TemplateOptions(args)

    input_path = options.input
    output_path = options.output
    statuses = tuple(s.strip() for s in options.statuses.split(",") if s.strip())

    print(f"input    = {input_path}")
    print(f"output   = {output_path}")
    print(f"statuses = {statuses}")

    if not input_path or not output_path:
        print("input and output are required")
        return 2

    with beam.Pipeline(options=options) as p:
        rows = (
            p
            | "Read" >> beam.io.ReadFromText(input_path)
            | "Parse" >> beam.Map(lambda line: line.split(","))
            | "Valid" >> beam.Filter(lambda row: len(row) > 6 and row[6] in statuses)
            | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
            | "SumRevenue" >> beam.CombinePerKey(sum)
            | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
        )
        rows | "Write" >> beam.io.WriteToText(
            output_path, num_shards=1, shard_name_template=""
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
```

Two things to notice:

- `TemplateOptions` declares `--input`, `--output` and `--statuses`, so
  Beam parses them cleanly instead of warning about unknown flags.
- There is **no `apache-beam` import problem** — the SDK is already there on
  the worker. This file imports it because it runs locally too.

### Read the parameters the way a flex template does

The template above reads `sys.argv[1:]`. When Dataflow runs it, that argv
contains the `--parameters` keys. Here is the same thing, demonstrated
locally without touching GCS:

```python
import sys

from apache_beam.options.pipeline_options import PipelineOptions


class TemplateOptions(PipelineOptions):
    """Runtime options for the orders flex template."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--input", default="")
        parser.add_argument("--output", default="")
        parser.add_argument("--statuses", default="complete")


options = TemplateOptions(
    [
        "--input=gs://example-data-bucket/orders.csv",
        "--output=gs://example-data-bucket/summary",
        "--statuses=complete,shipped",
    ]
)

print("input   :", options.input)
print("output  :", options.output)
print("statuses:", options.statuses)
```

Expected output:

```text
input   : gs://YOUR_BUCKET/orders.csv
output  : gs://YOUR_BUCKET/summary
statuses: complete,shipped
```

### Run the template locally with the same parameters

```bash
cd data-engineering/data-Course/google/Dataflow

python resources/sample_data.py --output-dir ./sample_data

python templates/orders_etl.py \
  --input=./sample_data/orders.csv \
  --output=./out/flex_local \
  --statuses=complete
```

Because the local runner is the default, this needs no credentials and no
bill. The output is a single file:

```bash
cat out/flex_local*
```

### Add a DoFn class and turn on `save_main_session`

Now the version of the template that needs `save_main_session`:

```python
"""A flex template that uses a DoFn class, so it needs save_main_session."""
from __future__ import annotations

import sys

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


class TemplateOptions(PipelineOptions):
    """Runtime options for the orders flex template."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--input", default="")
        parser.add_argument("--output", default="")


class ParseOrderFn(beam.DoFn):
    """Parse one CSV line into a (region, revenue) pair."""

    def process(self, line: str):
        parts = line.split(",")
        if len(parts) < 8:
            return
        yield parts[3], float(parts[7])


def run(argv: list[str] | None = None) -> int:
    """Build and run the pipeline."""
    args = list(argv if argv is not None else sys.argv[1:])
    # save_main_session lets the worker unpickle ParseOrderFn, which is
    # defined in __main__.
    args.append("--save_main_session=True")
    options = TemplateOptions(args)

    with beam.Pipeline(options=options) as p:
        rows = (
            p
            | "Read" >> beam.io.ReadFromText(options.input)
            | "Parse" >> beam.ParDo(ParseOrderFn())
            | "SumRevenue" >> beam.CombinePerKey(sum)
            | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
        )
        rows | "Write" >> beam.io.WriteToText(
            options.output, num_shards=1, shard_name_template=""
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
```

Run it locally the same way. Then note the difference when it goes to
Dataflow without `save_main_session`: the job fails at startup with an
attribute error about `ParseOrderFn`.

### Build and run on GCP

Everything below needs a project, a bucket, and the worker service account
with `roles/dataflow.worker`.

```bash
# 1. Upload the template
gcloud dataflow flex-template build orders-etl \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --template-file=./templates/orders_etl.py \
  --template-file-gcs-path=gs://YOUR_BUCKET/templates/orders-etl.py \
  --metadata="version=1.0.0,owner=data-platform" \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging \
  --requirements-file-requirements=google-cloud-bigquery==3.11.0

# 2. Run it
gcloud dataflow flex-template run orders-etl \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --template=gs://YOUR_BUCKET/templates/orders-etl.py \
  --temp-location=gs://YOUR_BUCKET/dataflow/temp \
  --staging-location=gs://YOUR_BUCKET/dataflow/staging \
  --service-account=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --parameters="input=gs://YOUR_BUCKET/orders.csv,output=gs://YOUR_BUCKET/summary,statuses=complete" \
  --wait=false

# 3. Confirm the template is registered
gcloud dataflow templates describe orders-etl \
  --project=YOUR_PROJECT_ID --region=us-central1
```

### Check the SDK version the service used

```bash
gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format='value(environment.sdkSupportStatus)'

gcloud dataflow jobs describe JOB_ID --project=YOUR_PROJECT_ID \
  --format=json | jq '.environment'
```

If the `sdkSupportStatus` is not the version you developed against, pin it
with `--sdk-location` at build time.

---

## 🛠️ Common Errors and Fixes

### `Can't pickle <class '__main__.ParseOrderFn'>`

```text
RuntimeError: Failed to pickle the pipeline.
Can't pickle <class '__main__.ParseOrderFn'>: attribute lookup
ParseOrderFn on __main__ failed
```

Your `DoFn` class is defined in `__main__` and `save_main_session` is off.
Add it:

```python
options = PipelineOptions(sys.argv[1:] + ["--save_main_session=True"])
```

### `AttributeError: module 'apache_beam' has no attribute 'io'`

```text
AttributeError: module 'apache_beam' has no attribute 'io'
```

Two causes. The first is a genuinely old SDK. The second, much more common
on a worker, is that you **bundled apache-beam** with `--py-files` or a
wheel, and your copy shadows the service's. Remove every copy of
`apache_beam` from what you ship.

### `ModuleNotFoundError: No module named 'transforms'`

```text
ModuleNotFoundError: No module named 'transforms'
```

Your template imports a local module that was never shipped. Either add it
to `--py-files`:

```bash
--py-files=./transforms.py
```

or inline the code into the template file.

### `ImportError: cannot import name 'BigQueryDisposition' from 'apache_beam.io'`

```text
ImportError: cannot import name 'BigQueryDisposition' from 'apache_beam.io'
```

This is a version mismatch — `BigQueryDisposition` moved or was added after
the SDK version the service ships. Use the import path that works across
versions:

```python
from apache_beam.io.gcp.bigquery import BigQueryDisposition
```

and check the service's SDK version with
`--format='value(environment.sdkSupportStatus)'`.

### The job fails immediately with no useful log

```text
Job failed with state FAILED. Worker logs are in Cloud Logging.
```

Read them:

```bash
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID" \
  --project=YOUR_PROJECT_ID --limit=100 --format=json \
  | jq -r '.[] | .textPayload // .jsonPayload.message // empty'
```

### The `--parameters` values are all empty

Your template read `sys.argv[1:]`, but Dataflow did not pass the individual
keys through. Declare them on a `PipelineOptions` subclass so Beam parses
them, and filter the argv to remove the raw `--parameters` string:

```python
class TemplateOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--input", default="")
        parser.add_argument("--output", default="")
```

### `The job cannot be started because the staging location is already in use`

Two jobs, one staging path. Use a unique path per run:

```bash
RUN_ID=$(date +%Y%m%d-%H%M%S)
STAGING=gs://YOUR_BUCKET/dataflow/staging/$RUN_ID
TEMP=gs://YOUR_BUCKET/dataflow/temp/$RUN_ID
```

### `pip install` failed on the worker

```text
ERROR: Could not find a version that satisfies the requirement ...
```

Your `--requirements-file-requirements` list contains an unpinned or
unavailable package. Pin exact versions and check they exist on PyPI for
the worker's Python version.

### The worker takes two minutes to start

That is the `--requirements-file-requirements` install. It happens on every
job start. If it is more than a couple of packages, consider a container
image instead — which is exactly what a flex template is *not*.

---

## 💡 Production Notes

- **Version-pin deliberately, and record the decision.** The default —
  develop against 2.77, run against whatever the service ships — is how
  you get a job that passed your tests and failed in production at 2am.
  Use `--sdk-location` for anything with a reliability commitment.
- **Do not ship `apache-beam`.** Not in `--py-files`, not in the
  requirements list, not vendored into a directory. The worker has it.
  Shipping a second copy is the single most reliable way to produce
  unpicklable, unexplainable failures.
- **Ship `--py-files` from a known directory.** The paths are relative to
  your shell's current directory. Run the `build` from the directory that
  contains the files, or use absolute paths — but absolute paths break a
  CI checkout that moves. Relative-to-the-repo-root is the sane convention.
- **Keep `--requirements-file-requirements` short.** Every package is an
  install on every worker at every job start. Two packages is fine; thirty
  is a thirty-package install race on every launch. If you need thirty
  packages, you need a container image and a different deployment tool.
- **Treat the GCS template path as mutable.** Anyone with write access to
  the bucket can change what the template does between two runs of the same
  job. In a regulated environment, write to a versioned prefix
  (`gs://bucket/templates/orders-etl/2026-10-28/`) and make the run
  reference the exact version.
- **Use `--metadata` as your version stamp.** It is free, it shows up in
  `gcloud dataflow templates describe`, and it answers "which version
  produced this number?" months later.
- **Set `--service-account` at build time** as well as run time. The
  staging objects are written by the identity that ran the `build`; if
  that is your personal account and you later delete it, the template is
  unusable.
- **The template file is code, so treat it like code.** It deserves a
  review, a lint, and a version bump in version control — even though it
  lives in a bucket.

---

## 🔑 Key Takeaways

- A flex template is **a Python file in GCS, run by path**. No image, no
  registry, no build step.
- `build` **uploads** the file; `run` **executes** it. `build` never
  creates a job.
- `--template-file` is **local**, `--template-file-gcs-path` is the
  **destination**, and `--template` is the **source at run time**. The two
  GCS paths must match exactly.
- The template must be **self-contained** (or use `--py-files`) and must
  **never bundle apache-beam**.
- `--py-files` ships your Python modules; `--requirements-file-requirements`
  installs third-party packages on the worker at job start.
- `--parameters="k=v,k2=v2"` becomes pipeline options. Read them with a
  `PipelineOptions` subclass so they parse cleanly.
- **`save_main_session=True`** is required whenever the template defines a
  `DoFn` class or uses module-level globals.
- The worker runs **the SDK version the service ships**, not the one you
  developed against. This is the biggest source of "works locally, fails
  in production".
- Pin the SDK with **`--sdk-location`**, or develop against the service's
  version, or feature-detect.

---

## 📚 Practice Exercises

1. **Write a template with three parameters.** Build
   `templates/enrich_orders.py` that takes `--input`, `--output` and
   `--rate-table` as parameters. Declare them on a `PipelineOptions`
   subclass with defaults, use the rate table as a side input, and run it
   locally with the sample data. Expected: the output has a converted
   revenue column.

2. **Break `save_main_session` on purpose.** Take the `ParseOrderFn`
   version of the template, remove `--save_main_session=True`, and run it
   locally with the `DirectRunner`. Record the exact error. Then explain
   why the local runner fails differently from a Dataflow worker.

3. **Ship an extra module.** Split the template into `orders_etl.py` and
   `transforms.py`, build with `--py-files=./transforms.py`, and confirm
   the job runs. Then repeat the build from a *different* working
   directory and explain the failure.

4. **Find the service's SDK version.** Build a trivial template, run it,
   and read the SDK version from the job's environment and from the worker
   logs. Write down the exact commands. Then compare it with
   `apache_beam.__version__` in your virtualenv and explain the gap.

5. **Pin the SDK.** Build an SDK location on GCS from your local install
   and run the template with `--sdk-location` pointing at it. Verify the
   job's SDK version changed. Describe what you would need to do to make
   this reproducible in CI.

6. **Design a metadata scheme.** Propose a `--metadata` format for your
   team: which keys, what values, and how a reader would use them during
   an incident. Write the exact `build` command with your metadata.

---

## 📖 Further Reading

- Google Cloud Dataflow flex templates — https://cloud.google.com/dataflow/docs/guides/templates/creating-flex-template
- Google Cloud Dataflow templates overview — https://cloud.google.com/dataflow/docs/guides/templates/overview
- Dataflow pipeline options — https://cloud.google.com/dataflow/docs/guides/pipeline-options
- Apache Beam Python SDK options — https://beam.apache.org/documentation/sdk/pipeline-options/
- Apache Beam: Python SDK developer guide — https://beam.apache.org/documentation/sdks/python/python-sdk-user-guide/
- Apache Beam: Beam SDK release notes — https://beam.apache.org/release/
