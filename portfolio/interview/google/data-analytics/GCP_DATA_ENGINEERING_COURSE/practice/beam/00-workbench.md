# 00 — The Beam Workbench

> **Practice Module 00 · Beam · 25 minutes**

## 🎯 What you will learn

- What a *workbench* is for Beam, and how it differs from a plain Python environment.
- The two ways to get one: Vertex AI Workbench notebooks, and a local environment you control.
- How the **Beam interactive runner** lets you validate a single PCollection before you
  run the whole job.
- The exact commands that turn a fresh checkout into a working Beam environment.
- How this course's workbench resolves its interpreter, and why that matters when you
  have more than one Python on your machine.

---

## 🧠 Concept

### What "workbench" means here

A **workbench** is a place to build and run pipelines interactively, rather than as a
submitted job. For Beam it is usually a Jupyter notebook, because the unit of work in a
Beam pipeline is a *graph of transforms* — and a graph is much easier to reason about
when you can look at it.

There are two places to get one.

| | Vertex AI Workbench | Local environment |
|---|---|---|
| What it is | A managed VM (user-managed notebook) with JupyterLab | A venv on your own machine |
| Beam included | Yes — plus the Google Cloud connector dependencies | You install them |
| Needs a GCP project | Yes | No |
| Data access | Direct, from GCS / BigQuery / Pub/Sub | Local files; cloud access needs credentials |
| Cost | A running VM costs money | Free |
| Best for | Building the real pipeline against real data | Learning the model; keeping the module verified |

The Vertex AI Workbench route has a genuine advantage: **the notebooks ship with Apache
Beam and the Google Cloud connector dependencies already installed.** You are not fighting
`pip`; you are writing pipeline code.

The local route has a different advantage, and it is the one this course takes: **it can
be verified.** Every "Expected output" in this suite was produced by an actual execution
here, and a validator re-runs the code and diffs the output. A Vertex notebook can show
you a pipeline working; it cannot prove that the text in a course matches reality.

### The Beam interactive runner

Ordinary Beam execution is all-or-nothing: you build the graph, you run it, you get
results at the end. The **interactive runner** (`apache_beam.runners.interactive`)
inserts itself between the two, so you can stop partway.

It gives you three things.

1. **Validate an individual PCollection.** `ib.collect(pc)` runs the pipeline *up to
   that PCollection* and hands you the actual elements — as a pandas DataFrame, not a
   summary, not a sample. The real output of that stage.
2. **Inspect the pipeline graph.** `ib.visualize(pipeline)` renders the transform graph.
3. **Keep the state.** Because the graph is retained, you can add another transform to
   the same PCollection without rebuilding everything before it.

That is the workflow the interactive runner is built for: build one step, check what it
actually produced, correct it, add the next step.

> **The interactive runner needs IPython.** Outside a notebook or an IPython shell it
> refuses to run, and says so: *"You cannot use Interactive Beam features when you are
> not in an interactive environment such as a Jupyter notebook or ipython terminal."*
> That is a real constraint, and it is why this module's blocks below are written to run
> under a plain interpreter — they use the ordinary runner, which is what you want for
> anything you intend to ship.

---

## 🛠️ Hands-On

### 💻 Runs locally — check your Beam installation

Start with the version, because the API surface moves between releases.

```python
import pkgutil

import apache_beam as beam
import apache_beam.runners as runners

print(f"beam version: {beam.__version__}")

# The runner modules this build ships with.
names = sorted(
    m.name for m in pkgutil.iter_modules(runners.__path__)
    if not m.name.startswith("_")
)
print(f"runner modules: {len(names)}")
print(", ".join(names))
```

Expected output:

```text
beam version: 2.77.0
runner modules: 23
common, common_test, dask, dataflow, direct, interactive, internal, job, pipeline_context, pipeline_context_test, pipeline_utils, pipeline_utils_test, portability, render, render_test, runner, runner_test, sdf_utils, sdf_utils_test, test, trivial_runner, trivial_runner_test, worker
```

### 💻 Runs locally — the interactive runner's API surface

```python
import apache_beam.runners.interactive.interactive_beam as ib

for name in ("collect", "show", "visualize", "display"):
    print(f"  {name}: {hasattr(ib, name)}")
```

Expected output:

```text
  collect: True
  show: True
  visualize: True
  display: False
```

`ib.collect` is the important one. It runs the pipeline up to that point and returns
the real elements, so a wrong assumption about what a transform produced becomes
visible immediately — rather than as a wrong number in a table three stages later.

`ib.visualize` is the graph function. Note that it lives on the *interactive* module,
not on the `Pipeline` object: `ib.visualize(pipeline)`, not `pipeline.visualize()`.

### 💻 Runs locally — a whole pipeline, start to finish

The interactive runner is for exploring. For the actual pipeline, use a normal runner.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=DirectRunner",
    "--environment_type=LOOPBACK",
])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3, 4, 5])
        | "Double" >> beam.Map(lambda x: x * 2)
        | "Keep big" >> beam.Filter(lambda x: x > 4)
        | "Key it" >> beam.Map(lambda x: ("k", x))
        | "Sum" >> beam.CombinePerKey(sum)
    )
```

Expected output:

```text
```

(The pipeline prints nothing on success — a Beam pipeline writes its results to its
sinks, not to stdout. That silence is what success looks like.)

Note the two extra steps. `CombinePerKey` operates on **key-value pairs**, not on bare
elements; feeding it a `PCollection` of ints raises:

```text
TypeCheckError: The transform 'Sum' requires PCollections of type
'Tuple[TypeVariable[K], Any]' but was applied to a PCollection of type
'<class 'int'>' (produced by the transform 'Keep big').
```

### 💻 Runs locally — the workbench this course uses

```python
import subprocess
import sys

sys.path.insert(0, ".")
from beam_lib import COURSE, REPO

# The same search order the workbench CLI uses.
candidates = [
    ("repo .env", REPO / ".env" / "bin" / "python"),
    ("project .beam-venv", COURSE / "practice" / ".beam-venv" / "bin" / "python"),
]

for label, candidate in candidates:
    if not candidate.exists():
        print(f"MISSING  {label}")
        continue
    probe = subprocess.run(
        [str(candidate), "-c", "import apache_beam"],
        capture_output=True,
        text=True,
    )
    if probe.returncode == 0:
        version = subprocess.run(
            [str(candidate), "-c", "import apache_beam; print(apache_beam.__version__)"],
            capture_output=True, text=True,
        ).stdout.strip()
        print(f"BEAM OK  {label}  (version {version})")
    else:
        print(f"NO BEAM  {label}")
```

Expected output:

```text
MISSING  repo .env
BEAM OK  project .beam-venv  (version 2.77.0)
```

---

## 🛠️ Common Errors and Fixes

### `ModuleNotFoundError: No module named 'apache_beam'`

You are running the system Python, not the environment Beam is installed in. The
workbench CLI resolves this for you; from a raw shell, check with
`python -c "import apache_beam"` and then use that same interpreter.

### `pip install apache-beam` → "externally-managed-environment"

PEP 668 protects the system Python on macOS and Debian. Create a virtual environment
instead:

```bash
python3 -m venv practice/.beam-venv
practice/.beam-venv/bin/python -m pip install apache-beam
```

### `ValueError: Unable to get filesystem from specified path` for a `gs://` path

Beam has no GCS client without the extra dependencies. Either install
`apache-beam[gcp]`, or — as this course's labs do — read the local copy of the data
from `Lab-sessions-beam-dataflow/sample_data/`.

### "You cannot use Interactive Beam features when you are not in an interactive environment"

The interactive runner requires IPython. `pip install ipython` is enough to get
`ib.collect` working under a plain script; a real notebook frontend is needed for the
richer visualisation features.

### `TypeCheckError: The transform 'Sum' requires PCollections of type ...`

`CombinePerKey` and `GroupByKey` need key-value pairs. Map to a `(key, value)` tuple
first.

---

## 💡 Production Notes

- **Pin the SDK version.** Dataflow runs the version you uploaded. A pipeline that
  works on Beam 2.61 and breaks on 2.77 is a dependency problem, not a logic problem.
- **Vertex AI Workbench instances are VMs and they cost money.** Stop them when you
  are not using them.
- **The interactive runner is a development tool.** It materialises results in the
  driver's memory; it is not how you run production pipelines.
- **A local environment that can run the pipeline is a test suite.** The point of
  verifying every expected output is that the code is proven to work before it ever
  reaches a cloud job.

---

## 🔑 Key Takeaways

- A Beam workbench is a Jupyter environment with Beam and the Cloud connectors
  already installed — Vertex AI Workbench provides that, or you build it locally.
- The **interactive runner** is the tool that makes pipeline development iterative:
  `ib.collect(pc)` shows you what one stage actually produced.
- `ib.visualize(pipeline)` shows the transform graph — it is a function on the
  interactive module, not a method on `Pipeline`.
- The interactive runner needs IPython; everything else in Beam does not.
- The course verifies every expected output by executing the code, so the numbers in
  these modules are not assertions — they are transcripts.

---

## 📚 Practice Exercises

1. Run `ib.collect` on the `source` PCollection *before* the `Double` transform.
   What is the difference, and what does it tell you about where a bug entered?
2. Add a third transform to the pipeline above and use `ib.visualize` to confirm the
   graph has the steps you expect.
3. Break the `Keep big` filter (change `> 4` to `> 40`) and use `ib.collect` to see
   the empty result. What would that look like if it had reached the sink instead?

---

## 📖 Further Reading

- Apache Beam documentation: <https://beam.apache.org/documentation/>
- Beam's interactive runner: <https://beam.apache.org/documentation/runtime/interactive/>
- Vertex AI Workbench: <https://cloud.google.com/vertex-ai/workbench/docs/introduction>

---

**Next:** [01 — What Cloud Dataflow Is](01-what-is-dataflow.md)
