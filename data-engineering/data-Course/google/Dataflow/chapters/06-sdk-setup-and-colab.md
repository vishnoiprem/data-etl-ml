# 2.1 — SDK Setup & Google Colab

> **Section 2 · SDK & Core Transforms · Lecture 2.1 · 6:30**

## 🎯 What you will learn

- How to install Apache Beam, and what the difference is between the plain wheel and the `[gcp]` extras
- Which Python versions Beam supports (3.9–3.13) and why the version actually matters
- The virtualenv layout this course uses, and how to verify the install is correct
- How to install Beam in Google Colab, and the four Colab-specific gotchas that will bite you
- Why the course recommends running notebooks locally rather than in Colab — and how to do the download-and-run-locally workflow properly
- How to point a Colab notebook at the course project so your edits are not lost

---

## 🧠 Concept

### What "installing Beam" actually installs

`pip install apache-beam` sounds like one package. It is closer to a hundred,
and the difference between the plain install and the extras is the difference
between a 40 MB download and a 400 MB one.

| Install | What you get | Roughly | Use it for |
|---|---|---|---|
| `apache-beam` | the portable core: `PCollection`, `Map`, `CombinePerKey`, file/text/Avro/Parquet I/O, the `DirectRunner` | ~40–80 MB | Local development, everything in Module 2 and Module 3, unit tests |
| `apache-beam[gcp]` | the above plus `DataflowRunner`, `ReadFromBigQuery`, `WriteToBigQuery`, `ReadFromPubSub`, `WriteToPubSub`, GCS filesystem, and the Google API client libraries they need | ~400 MB | Anything that touches Google Cloud |
| `apache-beam[gcp,dataframe]` | adds the pandas-like DataFrame API (`beam.io.ReadFromCsv`, `beam.io.ReadFromJson`) | + ~100 MB | The DataFrame API — **not** used in this course |
| `apache-beam[all]` | everything, including testcontainers, Kafka, and the AWS connectors | > 1 GB | Rarely worth it |

The extras are additive. `apache-beam[gcp]` is always a superset of the plain
install, so installing the extras is the safe choice *if* you might ever
deploy. The cost is disk and install time, not correctness.

> **A trap worth naming.** `apache-beam[gcp]` pulls in `google-cloud-bigquery`,
> `google-cloud-pubsub`, `google-cloud-storage`, `google-cloud-dataflow`,
> `grpcio`, and `proto-plus`. Any of these can have a wheel conflict with an
> existing project. If `pip install apache-beam[gcp]` fails deep in the
> resolver with a `ResolutionImpossible` error, the fix is almost never to
> add more `--upgrade` flags. The fix is a clean virtualenv.

### The Python version matrix

Apache Beam 2.x supports **Python 3.9 through 3.13**. The window is not
arbitrary, and it moves: Beam drops a Python version roughly six months
after CPython's own end-of-life, and adds a new one once the release has a
full release cycle of green CI.

| Python | Beam 2.77 status | Notes |
|---|---|---|
| 3.9 | supported | Oldest supported. Some transitive deps have already dropped it. |
| 3.10 | supported | The safest choice if your org is on an older LTS. |
| 3.11 | supported | Very widely deployed; the pre-3.12 default for many teams. |
| 3.12 | supported | |
| 3.13 | supported | What this course is tested on. |

Why the version matters more than it looks:

1. **C-extension wheels.** Beam's Google Cloud dependencies ship binary
   wheels. A source build of `grpcio` on an unsupported interpreter version
   can take twenty minutes and then fail.
2. **`from __future__ import annotations` behaviour.** The course project
   uses PEP 563-style postponed annotations everywhere. Python 3.10 changed
   how `typing` generics are evaluated at runtime, and Beam's type-hint
   inference reads those annotations. A version mismatch shows up as
   confusing type-hint errors rather than as a version error.
3. **`match` statements and new syntax.** Not in the course code, but in
   yours.

Check what you have:

```bash
python3 --version
```

If you need a specific version and do not have it, `pyenv` is the least
friction path:

```bash
pyenv install 3.13.1
pyenv local 3.13.1
```

### The virtualenv layout this course uses

The course root is `data-engineering/data-Course/google/Dataflow/`, and the
virtualenv lives *inside* it as `.venv/`. That single choice buys three
things:

- **Self-contained.** `cd` into the course root and the environment is
  there. No "which Python is on my PATH" questions.
- **Disposable.** `rm -rf .venv` and re-create it, with zero risk to the
  rest of your machine.
- **Reproducible.** The venv is a build artifact, not a source artifact, so
  it is in `.gitignore` and never committed.

The layout inside the course root:

```text
data-engineering/data-Course/google/Dataflow/
├── .venv/                     # the virtualenv (gitignored)
├── chapters/                  # the prose you are reading
├── project/                   # the runnable pipeline code
│   ├── batch_pipeline.py
│   ├── streaming_pipeline.py
│   ├── beam_options.py
│   ├── transforms.py
│   └── requirements.txt
├── resources/                 # sample data generator, linter, reference docs
│   ├── sample_data.py
│   ├── audit_course.py
│   ├── SETUP.md
│   ├── CHEATSHEET.md
│   ├── GLOSSARY.md
│   └── FAQ.md
├── notebooks/                 # Jupyter notebooks
├── sample_data/               # generated dataset (gitignored)
└── out/                       # pipeline output (gitignored)
```

Two important consequences:

- **Everything runs from the course root.** The reader's working directory
  is the course root, so paths like `./sample_data/orders.csv` and
  `./out/summary` are relative to it.
- **`project/` is importable as a package of modules, not as a script
  path.** `batch_pipeline.py` does `sys.path.insert(0, str(Path(__file__).resolve().parent))`
  so that `from transforms import ...` works no matter where it is launched
  from. That is why you can run `python project/batch_pipeline.py` from the
  course root and it still finds its siblings.

### Verifying the install

An install that "worked" is not an install that works. Run all three of
these:

```bash
# 1. The version
.venv/bin/python -c "import apache_beam; print(apache_beam.__version__)"
```

```bash
# 2. The transforms the course depends on
.venv/bin/python -c "
import apache_beam as beam
print('Map           :', hasattr(beam, 'Map'))
print('FlatMap       :', hasattr(beam, 'FlatMap'))
print('CombinePerKey :', hasattr(beam, 'CombinePerKey'))
print('ReadFromText  :', hasattr(beam.io, 'ReadFromText'))
print('WriteToText   :', hasattr(beam.io, 'WriteToText'))
"
```

To see which runner the SDK resolves to, ask the options object rather
than the `Pipeline` class — `beam.Pipeline.__module__` prints
`apache_beam.pipeline`, which tells you nothing useful:

```bash
.venv/bin/python -c "
import sys
sys.path.insert(0, 'project')
from beam_options import build_options, resolve_runner

options = build_options([])
print('runner:', resolve_runner(options))
"
```

The course default is `BundleBasedDirectRunner`.

```bash
# 3. A real end-to-end pipeline through the local runner
.venv/bin/python -c "
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
opts = PipelineOptions(['--runner', 'BundleBasedDirectRunner'])
with beam.Pipeline(options=opts) as p:
    (
        p
        | 'Create' >> beam.Create([1, 2, 3])
        | 'Double' >> beam.Map(lambda x: x * 2)
        | 'Print'  >> beam.Map(print)
    )
"
```

The third one is the only check that matters. It proves the SDK imports,
the runner starts, and the pipeline executes. Every other check is a
proxy.

> **On the runner name.** `beam.Pipeline()` with no options uses the
> *Prism* runner — a fast Go-based direct runner — in Beam 2.60+. The
> course project deliberately defaults to `BundleBasedDirectRunner`
> (see `project/beam_options.py`, `DEFAULT_RUNNER`) because Prism does not
> yet support every trigger and windowing combination. Chapter 1 used the
> bare `beam.Pipeline()` because it only did `Map` and `Filter`, which
> Prism handles fine. For anything involving windows, pass the options
> explicitly.

---

## 🧠 Google Colab: the honest assessment

Colab is genuinely useful for a first look at Beam, and genuinely bad as a
course environment. Both statements are true, and the second one has
specific technical causes.

### What Colab gives you

- **A free CPU with no install step.** `!pip install apache-beam` and you
  are running in about ninety seconds.
- **A real notebook UI** with no local Python required.
- **A persistent-ish filesystem** at `/content`, backed by a disk image.

### What Colab costs you

### Gotcha 1: the wheel size

`apache-beam` in Colab pulls in the whole dependency tree — roughly 400 MB
installed. The download itself is fine on a normal connection, but:

- Colab instances have limited disk. The default image is around 20 GB, and
  Beam plus PyArrow plus the Google clients will eat a meaningful chunk.
- The install runs `pip`, which prints a lot of output. Scroll past it.
- A **runtime reset** wipes the install. This is the single most common
  Colab frustration: you spend ten minutes on a notebook, the runtime
  disconnects, and you wake up to `ModuleNotFoundError: No module named
  'apache_beam'`.

### Gotcha 2: Java for some transforms

This is the one that catches people out. **Some Beam transforms are
implemented in the Java SDK** and are exposed to Python through the Beam
Runner API's cross-language bridge. When you call one from Python on a
runner that has no JVM available, the failure surfaces as a confusing error
rather than a clear "install Java".

In Beam 2.77 specifically, `beam.io.ReadFromBigQuery` and
`beam.io.WriteToBigQuery` are implemented in the Java SDK and executed on
Java workers. The `DataflowRunner` always has a JVM available (it runs the
Java SDK harness). The local `DirectRunner` does not, and trying to run
those transforms on a bare local runner fails.

**In Colab specifically**, the runtime image ships with Java preinstalled,
so `WriteToBigQuery` and `ReadFromBigQuery` *will* attempt to start a JVM.
That is a second, more confusing problem: the JVM starts, spends thirty
seconds initialising, and then the transform fails for an unrelated reason
(most often missing credentials). If you are only learning the Beam model
in Colab, avoid the BigQuery transforms entirely and use `WriteToText` or
`WriteToParquet`.

For local work, if you genuinely need a JVM-backed transform against a
local runner, install a JRE and point `JAVA_HOME` at it:

```bash
# macOS
brew install openjdk@17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

# Debian/Ubuntu
sudo apt-get install -y openjdk-17-jre-headless
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Gotcha 3: `/content` is slow, and `/tmp` is not durable

Colab's `/content` directory is backed by a FUSE filesystem that maps to a
Google Drive-backed disk image. It is *persistent across runtime restarts*
but it is *not* a real local filesystem — it is slow, and random reads are
slower still. A Beam pipeline that writes many small shards to `/content`
will crawl.

`/tmp` is a real local disk. It is fast. It is also **wiped when the
runtime resets**.

The rule that falls out of this:

```text
Download your data into /tmp, not /content. Read your code from /content.
Never rely on either surviving a runtime reset.
```

### Gotcha 4: the 12-hour session limit

A Colab session is capped. The limit has historically been 12 hours of
wall-clock runtime, after which the session is terminated and the kernel
dies. Code cells that are still running are killed mid-execution.

For a Beam course, this matters in one specific way: a long-running local
pipeline that fans out to many threads will keep the session alive but will
be killed when the cap is hit, with **no partial output guarantee** and a
kernel that dies mid-write. If you are running a pipeline over a large
sample dataset in Colab, cap the work or run it locally.

### The verdict

| Task | Colab | Local venv |
|---|---|---|
| Learning the Beam model, small inputs | excellent | excellent |
| Editing the course project | poor (no persistence you can trust) | excellent |
| Running the course's own pipelines | poor (install, path, reset) | excellent |
| Deploying to Dataflow | awkward (credentials, no `gcloud`) | good (`gcloud` is local) |
| Reproducible results | poor | excellent |

The course therefore takes this position: **Colab is a fine place to try
five lines of Beam. It is the wrong place to do this course.** Use it as a
scratchpad if you like, and do the work locally.

### Installing Beam in Colab — the minimal cell

If you do want to use Colab, this is the cell that gets you a working
install with the fewest surprises:

```bash
# Cell 1: install. Restart the runtime after this cell
# (Runtime > Restart runtime), otherwise the freshly installed
# packages are not on the path yet.
!pip install --quiet apache-beam
```

Then, in a **separate** cell after the restart:

```python
# Cell 2: verify
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

print("beam:", beam.__version__)

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5])
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Print" >> beam.Map(print)
    )
```

Two details in that cell are deliberate:

- **`--runner BundleBasedDirectRunner`, not the default.** Colab's default
  in Beam 2.77 is Prism, which downloads a Go binary and starts a
  subprocess server. That works, but it is slower to start and it fails
  loudly on windowing. The bundle-based runner is pure Python and starts
  instantly.
- **Restarting the runtime after the install.** `pip install` into the
  running interpreter's `sys.path` sometimes works immediately and
  sometimes does not, because the `site-packages` directory was scanned at
  startup. Restarting is deterministic.

### A realistic Colab cell: read the sample data

```bash
# Cell 3a: generate the sample data. The generator writes
# deterministic data - the same bytes every run.
!pip install --quiet apache-beam
!python resources/sample_data.py --output-dir /tmp/beam_sample_data
```

```python
# Cell 3b: read the sample data.
# Work in /tmp: it is a real local disk. /content is slow and FUSE-backed.
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

DATA_DIR = "/tmp/beam_sample_data"

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Read" >> beam.io.ReadFromText(f"{DATA_DIR}/orders.csv")
        | "Count" >> beam.combiners.Count.PerKey()
        | "Print" >> beam.Map(print)
    )
```

### Pointing a Colab notebook at the course project

The realistic scenario: you cloned the course repo on your laptop, and you
want Colab to have access to `project/` and `resources/` so you can import
`transforms.parse_order_line` instead of retyping it.

**Option A — Google Drive (recommended).** Mount Drive, then add the course
folder to the path:

```python
# %% Mount Drive and locate the course folder
from google.colab import drive
drive.mount("/content/drive")

import sys
COURSE_ROOT = "/content/drive/MyDrive/data-engineering/data-Course/google/Dataflow"
sys.path.insert(0, f"{COURSE_ROOT}/project")

import apache_beam as beam
from transforms import parse_order_line, is_valid_order

print("course project importable")
```

Then reference the course data with the `COURSE_ROOT` prefix:

```python
ORDERS_CSV = f"{COURSE_ROOT}/sample_data/orders.csv"
```

**Option B — Git clone inside the notebook.** Colab's images ship with
`git`, so this works:

```bash
!git clone --depth 1 https://github.com/YOUR_ORG/YOUR_REPO.git /tmp/course
```

Note the placeholder: put your own repository URL in. Do not leave a
literal placeholder in a file you commit.

**Option C — upload a zip.** Use Colab's file uploader, unzip into `/tmp`,
and add the `project` directory to `sys.path`. This works but it is manual
and the uploaded copy drifts from your local copy.

### The workflow the course actually recommends

**Download the `.ipynb`, edit it locally, run it locally.**

The reason is not ideological. It is that the course's notebooks reference
files by relative path (`./sample_data/orders.csv`), import from `project/`,
and expect to write to `./out/`. Those paths only resolve inside the course
root, in the course virtualenv, where Beam is installed.

The workflow:

1. Open the notebook in Colab (File → Download IPYNB, or from the notebook's
   own menu).
2. Save it into `notebooks/` in your local course checkout.
3. Run it locally with the course venv:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
jupyter lab notebooks/
```

4. If you need a GPU or a bigger machine for one specific experiment, push
   just that notebook to Colab, copy it back, and diff it.

This gives you the best of both: a real local environment for the course
work, and Colab as an escape hatch for the occasional compute-heavy cell.

```bash
# Register the venv as a Jupyter kernel so the notebook uses it
.venv/bin/python -m ipykernel install --user --name beam-course \
    --display-name "Beam Course (apache-beam)"
```

After that, in JupyterLab the kernel picker offers **Beam Course
(apache-beam)**. Without this step, the notebook silently uses your system
Python and you get `ModuleNotFoundError: No module named 'apache_beam'`
after ten minutes of confusing debugging.

---

## 🛠️ Hands-On: Setting Up the Course Environment

This is the setup the rest of the course assumes. Do it once.

### Step 1 — create the virtualenv

```bash
cd data-engineering/data-Course/google/Dataflow

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Check that the venv is actually active before installing anything:

```bash
which python
python --version
```

`which python` must print a path containing `.venv/`. If it prints
`/usr/bin/python`, the activation did not take — this is the single most
common setup mistake.

### Step 2 — install the course requirements

```bash
pip install -r project/requirements.txt
```

This installs `apache-beam[gcp]`, the Google Cloud client libraries, and
Jupyter. If the resolver fights you, fall back to the two-step install that
`resources/SETUP.md` recommends:

```bash
pip install apache-beam
pip install google-cloud-storage google-cloud-pubsub google-cloud-bigquery google-cloud-dataflow
pip install jupyterlab ipykernel nbformat nbclient pytest
```

### Step 3 — verify

```bash
python -c "
import apache_beam as beam
print('apache-beam', beam.__version__)
"
```

```bash
python -c "
import sys
sys.path.insert(0, 'project')
from beam_options import describe_environment
for k, v in describe_environment().items():
    print(f'{k:20s} {v}')
"
```

### Step 4 — generate the sample data

```bash
python resources/sample_data.py --output-dir ./sample_data
```

```bash
ls -la sample_data/
wc -l sample_data/*.csv sample_data/*.ndjson
```

Expected shape:

```text
5001  sample_data/orders.csv          # header + 5000 orders
20001 sample_data/events.csv          # header + 20000 events
5000  sample_data/orders.ndjson
20000 sample_data/events.ndjson
50    sample_data/product_reference.ndjson
5     sample_data/malformed_orders.csv
```

The generator is seeded, so the bytes are identical on every machine. That
is deliberate — the expected outputs printed throughout this course are
stable because the inputs are.

### Step 5 — run the course pipeline end to end

```bash
python project/batch_pipeline.py \
    --input ./sample_data/orders.csv \
    --output ./out/summary
```

```bash
cat out/summary*
```

Expected output (order of rows varies — the runner does not guarantee it):

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

### Step 6 — check the linter

```bash
python resources/audit_course.py
```

Zero errors means the course's own Python code — and the snippets in every
chapter — parse, and that every `beam.<something>` referenced actually
exists in the installed SDK. Run it before you blame Beam for a
`AttributeError`.

### Step 7 — register the Jupyter kernel

```bash
python -m ipykernel install --user --name beam-course \
    --display-name "Beam Course (apache-beam)"
```

```bash
jupyter lab notebooks/
```

Pick the **Beam Course (apache-beam)** kernel.

### Step 8 — a smoke-test notebook

Create `notebooks/00_smoke_test.ipynb` with this content and run it:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner", "BundleBasedDirectRunner"])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5])
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Print" >> beam.Map(print)
    )
```

You should see `2 4 6 8 10` in the output, in some order.

---

## 🛠️ Common Errors and Fixes

### `ModuleNotFoundError: No module named 'apache_beam'`

The interpreter running the script is not the one with Beam installed. This
is the single most common error in the whole course, and it is almost always
an activation problem.

```bash
which python
pip show apache-beam
```

If `pip show` finds Beam but `which python` does not point into `.venv/`,
the venv is not activated. In a notebook, the kernel is wrong — re-run
Step 7 and pick the right kernel.

### `ERROR: Cannot install apache-beam[gcp] ... ResolutionImpossible`

A dependency conflict with an existing environment. The correct fix is a
clean virtualenv, not a cascade of `--upgrade` flags:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install apache-beam
pip install google-cloud-storage google-cloud-pubsub google-cloud-bigquery
```

### `ERROR: Could not find a version that satisfies the requirement apache-beam` on Python 3.14

You are on a Python version newer than the SDK supports. Beam 2.77 supports
3.9–3.13. Check with `python --version` and either switch interpreters or
use a container.

### `ModuleNotFoundError: No module named 'apache_beam.io'`

`beam.io` is a submodule. In practice `import apache_beam as beam` exposes
it, but if you are importing pieces directly, be explicit:

```python
import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText
```

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. Beam's message does not
say which:

```text
RuntimeError: Transform name is already used: 'Read'
```

Labels are scoped per pipeline. This is caught statically by the course
linter:

```bash
python resources/audit_course.py
```

### `AttributeError: module 'apache_beam' has no attribute 'io'` in Colab

Same submodule issue, but in Colab it usually means the runtime was reset
and the install is gone. Reinstall, then **restart the runtime**.

### `CalledProcessError` / `JavaNotFoundError` when using a BigQuery transform locally

The BigQuery transforms run on the Java SDK. The local `BundleBasedDirectRunner`
does not have a JVM harness. Either:

- install a JRE and set `JAVA_HOME` (see the Concept section), or
- use the `DataflowRunner`, where a JVM is always available.

For the purposes of this course, neither is needed — the BigQuery chapter
uses the Dataflow runner only.

### `FileNotFoundError: ./sample_data/orders.csv`

You skipped Step 4 of the hands-on:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

Also check your working directory. The course paths are relative to the
course root.

### Colab: `RuntimeError: It looks like you are running the pipeline with a Java-based transform on a runner that has no Java`

The BigQuery transforms are Java-based. In Colab, either use
`WriteToText`/`WriteToParquet` for local learning, or move to a
`DataflowRunner` job.

### Colab: the runtime reset mid-notebook and everything is gone

Expected behaviour, not a bug. Re-run the install cell and restart the
runtime. Anything you wrote in `/tmp` is gone; anything in `/content` may
still be there but is not guaranteed. This is the concrete reason the
course recommends working locally.

### `pip install` in Colab prints for five minutes and then the cell is "cancelled"

Either the disk filled up or the install hit a slow mirror. Check the
disk usage in the Colab UI, and run the install with `--quiet` so the
output does not dominate the cell.

---

## 💡 Production Notes

- **Pin your Beam version in any real project.** `apache-beam>=2.53.0` in a
  requirements file is fine for a course. In production, pin an exact
  version (`apache-beam[gcp]==2.77.0`) and upgrade deliberately. Beam
  releases monthly, and the Dataflow worker images lag the SDK by days to
  weeks. A version mismatch between your SDK and the worker image produces
  errors that look like runner bugs.
- **Always deploy with `--runner DataflowRunner` explicitly.** The default
  runner depends on how the SDK is invoked. Never let a production job
  accidentally run on a local runner because of a typo in a flag.
- **The virtualenv is not a deployment strategy.** Dataflow packages your
  pipeline into a wheel and ships it to workers. Your local `pip install`
  state does not travel with the job. If you rely on a package that is not
  in `apache-beam[gcp]`, add it to a `requirements.txt` and pass it with
  `--requirements_file`.
- **Keep the venv and the worker image in sync.** A local run that works
  and a Dataflow run that fails, with no code change, is almost always a
  dependency difference. Reproduce locally with the same constraints.
- **Colab is a teaching tool, not a deployment target.** It has no
  service-account integration, no `gcloud`, ephemeral disk, a 12-hour cap,
  and a reset that erases your environment. If you are deploying anything
  real, deploy from a laptop or CI.
- **Automate the environment check in CI.** The course linter
  (`resources/audit_course.py`) does this for the snippets. For a real
  project, run a tiny pipeline against the exact worker image you intend
  to use, as a smoke test, on every build.
- **Disk is the constraint in Colab, not RAM.** Beam plus the Google
  clients will take a couple of gigabytes. On a free Colab instance that
  is fine; on a small CI container it is not.
- **Cost of a mistake in a virtualenv setup:** hours. The cost of a mistake
  in a Dataflow job configuration — a wrong region, a missing staging
  bucket, a `DataflowRunner` invoked without `--project` — is real money.
  Every command in this course defaults to the local runner *for that
  reason*. Read `project/beam_options.py` before you change that.

---

## 🔑 Key Takeaways

- `apache-beam` is the portable core; `apache-beam[gcp]` adds the Google
  Cloud transforms and roughly ten times the download size. Install the
  extras if you might deploy; the local course work does not need them.
- Beam 2.77 supports **Python 3.9–3.13**. The version affects wheel
  availability and type-hint behaviour, not just syntax.
- The course venv lives at `<course-root>/.venv/` and is disposable. Never
  commit it; always activate it before installing.
- The only install check that matters is a **real pipeline run** — imports
  and `hasattr` checks are proxies.
- Colab's four gotchas: the **wheel size**, the **JVM** needed by
  BigQuery transforms, the **slow `/content` filesystem** versus fast but
  ephemeral `/tmp`, and the **12-hour session cap**.
- The course's own recommendation is **download the `.ipynb` and run it
  locally** in the course venv, with the venv registered as a Jupyter
  kernel. Colab is a scratchpad, not a course environment.
- Always pass `--runner` explicitly in production. The default runner is
  not a deployment decision you should inherit.

---

## 📚 Practice Exercises

1. **Build the environment from scratch.** Delete `.venv/`, recreate it
   with Python 3.13, install `project/requirements.txt`, and confirm the
   batch pipeline produces the exact output shown in this chapter. Then
   repeat the install with only `pip install apache-beam` (no extras) and
   determine empirically which transforms stop working. Report which ones,
   and the exact error each produces.

2. **Measure the cost of the extras.** Time and measure the disk footprint
   of `pip install apache-beam` versus `pip install apache-beam[gcp]` in two
   throwaway virtualenvs. Report install time, installed size, and the
   number of packages added. Then justify, in two sentences, which one the
   course should ship in `project/requirements.txt`.

3. **Write the environment check as a script.** Create
   `project/check_environment.py` that prints the Python version, the Beam
   version, the resolved runner name (via `beam_options.resolve_runner`),
   whether the runner is local (via `beam_options.is_local`), and whether
   `sample_data/orders.csv` exists. Exit with status 1 if Beam is missing
   or the sample data is absent. Add it to `resources/test_course.py` as a
   test.

4. **Colab migration.** Take any notebook you have written for this course
   and make it runnable in both places: locally in the course venv and in
   Colab. The trick is a path resolution block at the top — something like
   detecting `/content` and choosing the root accordingly — plus a guarded
   `!pip install` that only runs in Colab. Show the final cell.

5. **Diagnose the JVM problem.** Write a short explanation of why
   `beam.io.WriteToBigQuery` fails on `BundleBasedDirectRunner` with a
   Java-related error but succeeds on `DataflowRunner`, in terms of the
   Beam Runner API's cross-language bridge. Then find the JVM requirement
   in the Beam source (look in the installed
   `apache_beam/runners/` tree) and quote the file and line that starts
   the Java harness.

6. **Pin and defend.** Change `project/requirements.txt` to pin
   `apache-beam[gcp]==2.77.0` exactly. Then write a three-line rationale
   for why an exact pin is better than `>=` in a production project, and a
   three-line rationale for why `>=` is better in a course.

---

## 📖 Further Reading

- Apache Beam Python SDK installation guide — https://beam.apache.org/documentation/sdks/python/python-install/
- Apache Beam Python SDK documentation — https://beam.apache.org/documentation/sdks/python/
- Apache Beam Python release notes (for Python version support) — https://beam.apache.org/get-started/releases/
- Apache Beam "Beam SDKs" overview — https://beam.apache.org/documentation/sdks/
- Google Colab FAQ — https://research.google.com/colaboratory/faq.html
- Python Packaging User Guide: extras — https://packaging.python.org/en/latest/guides/writing-package-data/#extras-and-optional-dependencies
- Google Cloud Dataflow development environment setup — https://cloud.google.com/dataflow/docs/develop-guide/setup
