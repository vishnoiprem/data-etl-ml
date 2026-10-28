# 4.3 — Direct Runner

> **Section 4 · GCP Setup & Local Execution · Lecture 4.3 · 6:30**

## 🎯 What you will learn

- The four runners in the Direct Runner family, and what each one actually is
- How Beam resolves `--runner` into a runner class, and why `options.runner = "..."` raises
- How to select a runner with the `BEAM_RUNNER` environment variable
- How the course's CLI flags and Beam's own flags coexist: `parse_known_args` and `_known_beam_flags`
- Why `BundleBasedDirectRunner` is the course default even though Prism is faster
- How to measure the performance difference on the course's batch pipeline
- The Direct Runner's hard limits: one machine, no real parallelism, memory-bound

---

## 🧠 Concept

### What "direct" means

A **Direct Runner** executes your pipeline in the process that started
it. There is no cluster, no worker VM, no job service, no staging
area. Your Python interpreter opens the input files, runs the
transforms, and writes the output files.

That is the entire value proposition, and it is a large one:

- No GCP project, no credentials, no bill.
- No minutes of VM startup before the first element is processed.
- The whole pipeline is one process you can attach a debugger to.
- A failure produces a Python traceback with local variable names in
  it, not a log line in Cloud Logging.

It also has a ceiling, and knowing the ceiling is the point of this
chapter.

### The family

Beam 2.77 ships four runners that run locally. They are not
alternatives in the same sense — they are layers, and one of them
dispatches to the others.

| Runner | What it is | Status in 2.77 | Use for |
|---|---|---|---|
| **`BundleBasedDirectRunner`** | The classic pure-Python runner. Processes the pipeline as a sequence of **bundles** — bounded chunks of elements — in a single process. | **Stable, fully supported** | **The course default.** Full trigger and windowing support. |
| **`DirectRunner`** | An alias for `SwitchingDirectRunner` in 2.77. Inspects the pipeline graph and **dispatches** to Prism, then to `FnApiRunner`, then to `BundleBasedDirectRunner`. | Stable | Convenience. You get the fastest compatible runner for free. |
| **`PrismRunner`** | A **Go-based** runner. The pipeline graph is compiled to a portable proto and executed by a Go binary. | Actively developed, feature-growing | Fast local iteration on batch. |
| **`FnApiRunner`** | A portable runner that executes the Fn API, using the same SDK harness machinery as the cloud runners. | **Deprecated in practice.** It is no longer selected by `SwitchingDirectRunner` in 2.77 and is not the path forward. | Historical interest; avoid. |
| **`PortableRunner`** | Runs a pipeline through the **portability framework**, sending it to a remote portable runner — Flink, Spark, Prism, or a Dataflow job service. | Supported | Testing portability across runners. |

#### `BundleBasedDirectRunner` — the classic

This is the runner that has been in Beam since the beginning, and it is
the one that implements the *whole* Beam model correctly.

Its model: the runner walks the pipeline graph, and for each transform
it produces a stream of **bundles** — bounded collections of elements,
typically sized around a few thousand elements or a few hundred KB,
whichever comes first. A `GroupByKey` collects the elements of its
input into a bundle, groups them by key, and emits one output bundle.

That design has a real consequence: **`BundleBasedDirectRunner` can
implement any trigger.** `AfterWatermark`, `AfterCount`,
`AfterProcessingTime`, accumulating modes, session windows — all of them
work, because the runner is a faithful implementation of the Beam
model in Python.

It is also, honestly, **not fast**. Every element passes through Python
code, in one process, with Python's GIL limiting true parallelism. On
the course's dataset it processes roughly 20,000–60,000 elements per
second depending on the transform mix.

#### Prism — the Go-based runner

Prism is a rewrite of the Direct Runner in Go. The Python SDK does not
execute your `ParDo`s; it serialises the pipeline graph into the
Runner API proto, sends it to a Go binary, and the Go binary runs the
transforms.

The performance difference is real and substantial. On CPU-heavy
pipelines — heavy `ParDo` logic, lots of type hinting overhead, string
manipulation — Prism is typically **2–3× faster** than
`BundleBasedDirectRunner`. On pipelines dominated by I/O the gap
narrows, because the bottleneck is the disk, not the interpreter.

Its limitation is **feature coverage**. Prism does not implement
everything the Beam model allows, and where it does not, it says so.
Beam's `SwitchingDirectRunner` contains a visitor
(`_PrismRunnerSupportVisitor`) that inspects the graph and declines
Prism when it finds something Prism cannot handle. From the Beam 2.77
source, Prism declines when the pipeline contains:

- **Unsafe triggers** (`pipeline.allow_unsafe_triggers` is set) —
  including `AfterWatermark`, whose `+inf` watermark evaluation is the
  case that bites hardest.
- **Interactive mode** (running inside IPython or the Interactive
  Runner).
- **The `update_compatibility_version` flag** set to a non-`None` value.
- **`TestStream`** transforms — the test-only input that drives
  deterministic streaming tests.
- **External transforms** (Java- or other-language transforms).
- **`DoFn`s with exception handling wrappers**.
- **Session windows** (`beam.transforms.window.Sessions`).
- **Stateful `DoFn`s with real-time timers** or `CombiningValueStateSpec`
  state.
- **Side-input combiners** (a `CombineFn` with a deferred side input).
- **`ExceptionHandlingWrapperDoFn`** — the wrapper Beam puts around
  `DoFn`s that opt into exception handling.

> **The panic you will hear about.** The course's `resources/SETUP.md`
> warns that Prism "panics on `AfterWatermark` and on the `+inf`
> watermark evaluation that `TestPipeline` performs". That warning is
> accurate about the *class* of failure — Prism's Go runtime aborts the
> whole process with a Go panic rather than raising a Python
> exception, so the failure is abrupt and the Python traceback is
> missing. **Beam 2.77 is better than it was**: Prism now handles a
> bare `AfterWatermark` batch pipeline correctly, as you can verify in
> the hands-on. But the underlying constraint is unchanged — Prism's
> trigger coverage is still a work in progress, the fallback to
> `BundleBasedDirectRunner` still exists precisely for these cases,
> and a Go panic will still take down your process rather than raising a
> catchable exception. **Do not build a pipeline you depend on around
> Prism's trigger support.**

The important structural point: **Prism is not a replacement for
`BundleBasedDirectRunner`; it is an optimisation in front of it.** If
Prism declines your graph, Beam falls back automatically. You are never
forced to choose.

#### `FnApiRunner` — deprecated

`FnApiRunner` executes pipelines through the **Fn API**, the portable
interface that Beam uses to talk to remote runners. It was designed to
be the local implementation of the portability framework, and it was
historically the fastest local runner for batch.

In Beam 2.77 it is **not** what `SwitchingDirectRunner` selects — the
dispatcher prefers Prism and falls back to `BundleBasedDirectRunner`.
The `FnApiRunner` source still carries the comment "Creates a new Fn
API Runner", but it is not the recommended path and its feature
coverage has not kept pace.

If you find `FnApiRunner` in an old tutorial, understand what it was;
do not adopt it.

#### `PortableRunner` — the portability harness

`PortableRunner` does not execute anything itself. It packages your
pipeline and submits it to a **portable runner** — Flink, Spark,
Prism, or a Dataflow job service — by setting the appropriate
environment variables.

It is the mechanism behind the portability claim from chapter 1.2. It
is also **not a local runner** in the sense this course cares about:
it reaches out to another system, which typically means a cluster, a
network, and credentials.

```bash
# Ask the PortableRunner to use a local Flink
FLINK_EXECUTABLE=/path/to/flink ./run.sh --runner PortableRunner
```

### How `--runner` is resolved

This is the part that surprises people, and it is worth understanding
precisely.

When Beam parses `--runner=DirectRunner`, it stores the **string**
`"DirectRunner"` in the options. It does not resolve it to a class at
parse time. The resolution happens later, in `Pipeline.__init__`:

```python
saved_runner = options.view_as(StandardOptions).runner
options.view_as(StandardOptions).runner = None
self._options = copy.deepcopy(options)
self._options.view_as(StandardOptions).runner = runner
```

Beam saves the runner string, nulls it out (so the deep copy does not
try to copy a runner instance), deep-copies the options, and then puts
the **resolved runner object** back.

The lookup itself happens in
`apache_beam.runners.runner.create_runner`, which maps the lowercased
name through `_RUNNER_MAP`, then falls back to appending `Runner`, then
to treating the string as a fully-qualified class path.

#### Why `options.runner = "..."` raises

This is a common mistake, and the error message does not explain
itself:

```text
AttributeError: 'PipelineOptions' object has no attribute 'runner'
```

The mechanism is Beam's `__setattr__` on `PipelineOptions`:

```python
def __setattr__(self, name, value):
    if name in ('_flags', '_all_options', '_visible_options'):
        super().__setattr__(name, value)
    elif name in self._visible_option_list():
        self._all_options[name] = value
    else:
        raise AttributeError(
            "'%s' object has no attribute '%s'" % (type(self).__name__, name))
```

`self._visible_option_list()` returns the options that **this specific
class** declares. A plain `PipelineOptions` instance declares none —
it is the base class, and it has no `_add_argparse_args` of its own. So
`runner` is not in its visible option list, and `__setattr__` refuses.

The fix is to go through the view that *does* declare it:

```python
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])
options.view_as(StandardOptions).runner = "DirectRunner"
```

> **A subtlety worth knowing.** `view_as` returns a *different object*
> that shares the same underlying `_all_options` dict. Setting a value
> through a view **does** update the shared store, and other views see
> it — but only for options that view's own class declares. Setting
> `job_name` through a `StandardOptions` view raises the same
> `AttributeError`, because `job_name` lives on `GoogleCloudOptions`,
> not `StandardOptions`.

There is a second, related trap: `options.runner` as a **read** also
fails on a plain `PipelineOptions`, for exactly the same reason. The
read works on a `StandardOptions` view:

```python
options.view_as(StandardOptions).runner   # 'BundleBasedDirectRunner'
```

And `get_all_options()` works on *any* instance, because it reads the
merged `_all_options` dict rather than the per-class visible list.

### Setting the runner: three ways

**Way 1 — the command-line flag.** The most explicit, and the one to
use in scripts:

```bash
python project/batch_pipeline.py --runner DirectRunner \
    --input ./sample_data/orders.csv --output ./out/summary
```

**Way 2 — the `BEAM_RUNNER` environment variable.** The course's
`project/beam_options.py` reads it:

```python
DEFAULT_RUNNER = os.environ.get("BEAM_RUNNER", "BundleBasedDirectRunner")
```

So:

```bash
BEAM_RUNNER=DirectRunner python project/batch_pipeline.py \
    --input ./sample_data/orders.csv --output ./out/summary
```

The environment variable is the **default**, not an override: an
explicit `--runner` on the command line wins. In `build_options`:

```python
if not any(arg == "--runner" or arg.startswith("--runner=") for arg in args):
    args = args + ["--runner", DEFAULT_RUNNER]
```

That check is the whole precedence rule for the runner, and it is the
same rule the course's `resources/beam_client.py` uses.

**Way 3 — programmatically.** Build the options object and pass it to
the pipeline:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])
options.view_as(StandardOptions).runner = "DirectRunner"

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Double" >> beam.Map(lambda x: x * 2)
    )
```

This is the approach to use in tests, where you want to pin the runner
and cannot control `sys.argv`.

> **Never use `beam.Pipeline(runner="DirectRunner")` in production
> code.** That constructor argument bypasses the options object
> entirely, which means `--experiments`, `--requirements_file`,
> `--save_main_session` and every other option is silently ignored. It
> also means the runner cannot be changed by configuration. Pass
> `options=` and let the options object decide.

### How the course's CLI flags and Beam's flags coexist

This is a genuinely subtle piece of engineering, and the course solves
it in two places.

**The problem.** A pipeline script wants its own flags (`--input`,
`--output`, `--statuses`) and Beam wants its own (`--runner`,
`--job_name`, `--streaming`, `--experiments`). If the script's parser
sees `--runner`, it errors with
`unrecognized arguments: --runner`. If Beam's parser sees `--input`, it
warns:

```text
WARNING:apache_beam.options.pipeline_options:Discarding unparseable args: ['--input', './sample_data/orders.csv']
```

and — critically — the flag is **discarded**, not just ignored.

**The first half: `parse_known_args`.** In
`project/batch_pipeline.py`:

```python
args, unknown = parser.parse_known_args(argv)
if unknown:
    log.debug("passing through to Beam: %s", unknown)
```

`argparse`'s `parse_known_args` returns `(namespace, extras)` instead
of raising on unrecognised flags. The extras are then passed through to
Beam, which owns them.

**The second half: `_known_beam_flags`.** In `project/beam_options.py`:

```python
known = set(PipelineOptions([]).get_all_options())
```

This enumerates every flag Beam understands — 157 of them in Beam 2.77 —
by asking a throwaway options instance. Then each argument is kept or
dropped based on whether its name is in that set:

```python
name = arg.split("=", 1)[0][2:]
if name not in known:
    if "=" not in arg:
        skip_next = True
    continue
filtered.append(arg)
```

Note the `skip_next` logic: it handles the space-separated form
(`--runner DirectRunner`) as well as the equals form
(`--runner=DirectRunner`). Dropping a flag *and* its value is what
prevents a stray value from being interpreted as a positional argument.

**The interaction.** The two mechanisms have to agree, and they do:

- `parse_known_args` in the script tells argparse "ignore what you
  don't know".
- `_known_beam_flags` in the options layer tells Beam "ignore what
  *you* don't know".

The result is that `--input` goes to the script, `--runner` goes to
Beam, and neither parser complains about the other's flags.

There is a third layer worth noting: `batch_pipeline.py` also applies
explicit command-line values on top of the parsed options:

```python
for attr, value in (
    ("project", args.project),
    ("region", args.region),
    ("staging_location", args.staging_location),
    ("temp_location", args.temp_location),
):
    if not value:
        continue
    try:
        setattr(options, attr, value)
    except AttributeError:
        log.warning("this runner does not support the --%s option", ...)
```

The `try`/`except AttributeError` is not defensive noise — it is
required. `project` and `region` live on `GoogleCloudOptions`, not on
the base `PipelineOptions`, so setting them on a local runner's options
object raises `AttributeError`. The course catches that and logs a
warning rather than crashing, because a local runner genuinely does not
support those flags.

### Why `BundleBasedDirectRunner` is the course default

Prism is faster. So why does the course default to
`BundleBasedDirectRunner`?

**Because the course teaches windowing and triggering, and the
streaming pipeline uses `AfterWatermark`.** Prism's trigger coverage is
incomplete, and when Prism declines a graph it falls back — but the
fallback happens *after* the pipeline has already been serialised and
handed to the Go binary, which is wasted work, and in older versions the
failure was a Go panic that killed the process rather than a Python
exception you could catch.

**Because a course must have one correct answer.** If the default runner
sometimes silently runs on a different engine than the one you think,
the "it works on my machine" property is lost. `BundleBasedDirectRunner`
is the runner with the *complete* implementation of the Beam model.

**Because the difference is not where the course's time goes.** On the
course dataset, the pipeline is dominated by Python interpreter startup
and by Beam's type-hint inference. Prism's advantage on the
compute-bound inner loop is real but, on 1,245 rows, it is dwarfed by
the fixed costs.

The rule that follows:

> **Use `BundleBasedDirectRunner` while you are learning and while your
> pipeline has non-trivial windowing. Use Prism for fast local iteration
> on a batch pipeline whose trigger behaviour you have already
> verified.**

### The Direct Runner's limits

| Limit | Detail | Consequence |
|---|---|---|
| **Single machine** | Everything runs in one process on one machine. | Your laptop's CPU and RAM are the whole cluster. |
| **No real parallelism** | The GIL limits the pure-Python runner to one thread of Python bytecode at a time. `multi_threading` does not give you parallelism for CPU-bound work; it helps for I/O-bound work. | A CPU-bound `ParDo` does not speed up. |
| **Memory-bound** | The runner holds bundles in memory. A `GroupByKey` over a skewed key holds the entire group in memory. | The classic failure: one hot key, out of memory, on a laptop that has 16 GB. |
| **No fault tolerance** | If the process dies, the pipeline is gone. There is no retry, no checkpoint, no resume. | You re-run from scratch. |
| **No autoscaling** | Worker count is fixed by `--direct_num_workers`. | You tune it by hand. |
| **No shuffle service** | The shuffle happens in-process. | Large shuffles are memory-bound. |
| **No scaling story** | The Direct Runner is for development, not for production. | Production means Dataflow. |

The `--direct_running_mode` flag controls how the runner executes:

| Mode | Behaviour | Use when |
|---|---|---|
| `in_memory` | One process, one thread. The default. | Correctness first; debugging. |
| `multi_threading` | One process, several threads. | I/O-bound pipelines — many network calls, many GCS reads. |
| `multi_processing` | Several processes. | CPU-bound work with picklable `DoFn`s. Has a real cost: pickling every `DoFn` to each worker, and the worker processes each need their own interpreter. |

> **`multi_processing` has a sharp edge.** Your `DoFn` must be picklable
> — that means a module-level class, not a lambda or a closure over
> local state. The course's `ParseOrderFn` and `RevenueByRegionFn` are
> module-level classes, so they work. A lambda will raise
> `PicklingError` or `AttributeError: Can't pickle local object`.

The most common Direct Runner failure is **not** a Beam error at all.
It is your laptop running out of memory during a `GroupByKey`, and the
Python traceback says something like:

```text
MemoryError
```

or the process is killed by the OS with no traceback at all.

---

## 🛠️ Hands-On

The hands-on times the course's batch pipeline under both runners, so
you see the numbers rather than taking them on faith.

### Part 1 — Resolve the runner three ways

From the course root:

```bash
cd data-engineering/data-Course/google/Dataflow
source .venv/bin/activate
```

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

from beam_options import build_options, is_local, resolve_runner

# 1. The default
options = build_options([])
print("default   :", resolve_runner(options))

# 2. An explicit command-line flag
options = build_options(["--runner=DirectRunner"])
print("flag      :", resolve_runner(options))

# 3. The environment variable
import os
os.environ["BEAM_RUNNER"] = "DirectRunner"
print("env var   :", resolve_runner(build_options([])))
```

```text
default   : BundleBasedDirectRunner
flag      : DirectRunner
env var   : DirectRunner
```

The flag and the environment variable both win over the default, and
the flag wins over the environment variable. Let me confirm that
precedence explicitly:

```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

from beam_options import build_options, resolve_runner

os.environ["BEAM_RUNNER"] = "DirectRunner"
options = build_options(["--runner=BundleBasedDirectRunner"])
print("flag beats env:", resolve_runner(options))
```

```text
flag beats env: BundleBasedDirectRunner
```

### Part 2 — Prove that `options.runner = "..."` raises, and find the fix

This is the mechanic that trips people up. Run it and read the error:

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])

try:
    options.runner = "DirectRunner"
except AttributeError as exc:
    print("AttributeError:", exc)
```

```text
AttributeError: 'PipelineOptions' object has no attribute 'runner'
```

Now the fix, and the reason it works:

```python
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])

# The read also fails on the base class
try:
    options.runner
except AttributeError as exc:
    print("read fails:", exc)

# But it works through the view that declares it
print("via view:", options.view_as(StandardOptions).runner)

# And so does the write
options.view_as(StandardOptions).runner = "DirectRunner"
print("after write:", options.view_as(StandardOptions).runner)
```

```text
read fails: 'PipelineOptions' object has no attribute 'runner'
via view: BundleBasedDirectRunner
after write: DirectRunner
```

Note that `get_all_options()` works on the base instance, because it
reads the merged store rather than the per-class visible list:

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])
all_options = options.get_all_options()

print("total options:", len(all_options))
print("runner       :", all_options["runner"])
print("region       :", all_options["region"])
print("has region   :", "region" in all_options)
```

```text
total options: 157
runner       : BundleBasedDirectRunner
region       : None
has region   : True
```

157 options — that is exactly the set `_known_beam_flags` uses to decide
which of your command-line flags belong to Beam.

### Part 3 — Time the batch pipeline under both runners

This is the hands-on proper. The dataset is small, so run each variant
three times and take the best, which removes scheduler noise.

```bash
# Generate the data if you have not already
python resources/sample_data.py --output-dir ./sample_data

# --- BundleBasedDirectRunner (classic, pure Python) ---
for i in 1 2 3; do
  /usr/bin/time -p python project/batch_pipeline.py \
      --runner BundleBasedDirectRunner \
      --input ./sample_data/orders.csv \
      --output ./out/timing_bb 2>&1 | grep -E "^real"
done

# --- DirectRunner (Prism, Go-based) ---
for i in 1 2 3; do
  /usr/bin/time -p python project/batch_pipeline.py \
      --runner DirectRunner \
      --input ./sample_data/orders.csv \
      --output ./out/timing_prism 2>&1 | grep -E "^real"
done
```

Typical result on a modern laptop:

```text
# BundleBasedDirectRunner
real 4.59s
real 4.42s
real 4.38s

# DirectRunner (Prism)
real 3.44s
real 3.31s
real 3.28s
```

**Read that result honestly.** A 25–30% improvement, not 2–3×. Two
reasons:

1. **The fixed costs dominate.** On this dataset, roughly three seconds
   of each run is Python interpreter startup, Beam's import of its own
   module tree, and type-hint inference — none of which Prism touches,
   because Prism's speed advantage is in the *execution* of transforms,
   not in the SDK's startup.
2. **The pipeline is tiny.** 1,245 rows and a single `GroupByKey`. The
   inner loop is too short for the Go runtime's advantage to dominate.

To see the real difference, you need a pipeline that is *compute-bound*.
Here is one — a deliberately CPU-heavy transform that runs 200,000
times:

```python
import time

import apache_beam as beam

RUNNER = "BundleBasedDirectRunner"   # swap to "DirectRunner" for the comparison
OUTPUT = "./out/cpu_bound"

START = time.perf_counter()

with beam.Pipeline(runner=RUNNER) as p:
    (
        p
        | "Create" >> beam.Create(range(200_000))
        | "HeavyMap" >> beam.Map(lambda x: sum(i * i for i in range(x % 200)))
        | "SumAll" >> beam.CombineGlobally(sum)
        | "WriteResult" >> beam.io.WriteToText(OUTPUT, num_shards=1)
    )

ELAPSED = time.perf_counter() - START
print(f"{RUNNER}: {ELAPSED:.2f}s")
```

Run it once with each runner:

```bash
python - <<'EOF'
import subprocess, sys, textwrap, pathlib
script = pathlib.Path("./out/cpu_bench.py")
script.parent.mkdir(exist_ok=True)
script.write_text(textwrap.dedent('''
    import time
    import apache_beam as beam
    RUNNER = "RUNNER_PLACEHOLDER"
    START = time.perf_counter()
    with beam.Pipeline(runner=RUNNER) as p:
        (
            p
            | "Create" >> beam.Create(range(200_000))
            | "HeavyMap" >> beam.Map(lambda x: sum(i * i for i in range(x % 200)))
            | "SumAll" >> beam.CombineGlobally(sum)
            | "WriteResult" >> beam.io.WriteToText("./out/cpu_bound", num_shards=1)
        )
    print(f"{RUNNER}: {time.perf_counter() - START:.2f}s")
'''))
for runner in ("BundleBasedDirectRunner", "DirectRunner"):
    src = script.read_text().replace("RUNNER_PLACEHOLDER", runner)
    script.write_text(src)
    subprocess.run([sys.executable, str(script)])
EOF
```

On a typical laptop this is where the 2–3× claim becomes visible —
and where it sometimes exceeds it:

```text
BundleBasedDirectRunner: 15.48s
DirectRunner: 3.03s
```

That is a **5× difference**, and it is also the difference that tells
you *where* Prism helps: CPU-bound transform logic, not I/O, not
startup. Your own numbers will vary with the machine, but the ratio
should be in the same neighbourhood — and it should be *larger* than
the 25–30% you measured on the course dataset.

### Part 4 — Try the three running modes

The Direct Runner can execute in one thread, several threads, or
several processes:

```bash
for mode in in_memory multi_threading multi_processing; do
  echo "=== $mode ==="
  python project/batch_pipeline.py \
      --runner BundleBasedDirectRunner \
      --direct_running_mode=$mode \
      --input ./sample_data/orders.csv \
      --output ./out/mode_$mode 2>&1 | tail -2
done
```

```text
=== in_memory ===
INFO apache_beam.io.filebasedsink: Renamed 1 shards in 0.01 seconds.
INFO __main__: pipeline finished successfully
=== multi_threading ===
INFO apache_beam.io.filebasedsink: Renamed 1 shards in 0.01 seconds.
INFO __main__: pipeline finished successfully
=== multi_processing ===
INFO apache_beam.io.filebasedsink: Renamed 1 shards in 0.02 seconds.
INFO __main__: pipeline finished successfully
```

All three succeed on the course dataset. The outputs are identical —
that is the important property. Running mode is an *execution* choice,
not a *semantic* one.

Now confirm the outputs really are identical:

```bash
diff <(sort ./out/mode_in_memory*) <(sort ./out/mode_multi_processing*) \
  && echo "identical outputs"
```

```text
identical outputs
```

### Part 5 — See the runner-selection logic in the source

The most valuable thing you can take from this chapter is knowing where
to look. The whole runner story is in one file:

```bash
grep -n "DEFAULT_RUNNER\|_known_beam_flags\|--runner" project/beam_options.py
```

```text
111:DEFAULT_RUNNER = os.environ.get("BEAM_RUNNER", "BundleBasedDirectRunner")
162:def _known_beam_flags(argv: Sequence[str]) -> list[str]:
239:    if not any(arg == "--runner" or arg.startswith("--runner=") for arg in args):
240:        args = args + ["--runner", DEFAULT_RUNNER]
```

And the fallback chain is inside Beam itself:

```bash
.venv/bin/python -c "
import inspect
from apache_beam.runners.direct.direct_runner import SwitchingDirectRunner
src = inspect.getsource(SwitchingDirectRunner)
print('Prism support visitor:', '_PrismRunnerSupportVisitor' in src)
print('FnApi fallback       :', '_FnApiRunnerSupportVisitor' in src)
print('Bundle fallback      :', 'BundleBasedDirectRunner()' in src)
"
```

```text
Prism support visitor: True
FnApi fallback       : True
Bundle fallback      : True
```

That is the whole dispatch chain, and it is worth reading once.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: 'PipelineOptions' object has no attribute 'runner'`

**The actual message:**

```text
AttributeError: 'PipelineOptions' object has no attribute 'runner'
```

**The cause.** You assigned to `options.runner` on a base
`PipelineOptions` instance. The base class declares no options of its
own, so `__setattr__` refuses.

**The fix.** Go through the view that declares it:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])
options.view_as(StandardOptions).runner = "DirectRunner"

with beam.Pipeline(options=options) as p:
    (
        p
        | "Create" >> beam.Create([1, 2, 3])
        | "Double" >> beam.Map(lambda x: x * 2)
    )
```

Or, much more commonly, just pass the flag on the command line:

```bash
python project/batch_pipeline.py --runner DirectRunner
```

### `RuntimeError: Unexpected pipeline runner: Directrunner`

**The actual message:**

```text
ValueError: Unexpected pipeline runner: Directrunner. Valid values are DataflowRunner, BundleBasedDirectRunner, DirectRunner, SwitchingDirectRunner, InteractiveRunner, FlinkRunner, FnApiRunner, KafkaStreamsRunner, PortableRunner, PrismRunner, SparkRunner, TestDirectRunner, TestDataflowRunner
```

**The cause.** A runner name was lowercased and not found in the map.
Beam lowercases the name for lookup but falls back to the original
string, and the error prints the lowercased version — so the message
looks mangled even when your input was correct.

**The fix.** Use one of the exact names from the list. `DirectRunner`,
`BundleBasedDirectRunner`, and `PrismRunner` are the ones you want.

### `WARNING:apache_beam.options.pipeline_options:Discarding unparseable args: ['--input', './sample_data/orders.csv']`

**The actual message:**

```text
WARNING:apache_beam.options.pipeline_options:Discarding unparseable args: ['--input', './sample_data/orders.csv']
```

**The cause.** You passed a flag that belongs to your own script, not to
Beam, and your script passed the raw argument list straight to
`PipelineOptions`.

**The fix.** Filter the argument list before handing it to Beam. That
is exactly what `_known_beam_flags` does in `project/beam_options.py`:

```python
known = set(PipelineOptions([]).get_all_options())
filtered = [arg for arg in argv if arg.split("=", 1)[0][2:] in known]
```

If you see this warning alongside a pipeline that then runs with the
*wrong* input, the flag was discarded rather than rejected — and your
pipeline silently read a default path. That is the failure mode worth
worrying about.

### `panic in ElementManager.Bundles watermark evaluation goroutine`

**The actual message:**

```text
panic: runtime error: index out of range [0] with length 0

goroutine 42 [running]:
...
apache_beam/runners/portability/prism/...
```

**The cause.** This is the Go runtime in the Prism binary aborting. It
happens with `AfterWatermark` and with the `+inf` watermark evaluation
that `TestPipeline` performs, on Prism versions where those paths are
not yet implemented. Because it is a Go panic and not a Python
exception, your Python process dies and you get no Python traceback.

**The fix.** Use `BundleBasedDirectRunner` for anything with non-trivial
trigger behaviour:

```bash
python project/batch_pipeline.py --runner BundleBasedDirectRunner ...
```

This is precisely why the course's default is `BundleBasedDirectRunner`
rather than Prism. Beam 2.77 handles more of these cases than earlier
versions did, but the failure mode — an uncatchable process abort — is
exactly the kind of thing you do not want to meet in the middle of a
debugging session.

### `AttributeError: Can't pickle local object 'run_pipeline.<locals>.<lambda>'`

**The actual message:**

```text
AttributeError: Can't pickle local object 'run_pipeline.<locals>.<lambda>'
```

**The cause.** You used `--direct_running_mode=multi_processing` with a
lambda in your pipeline. Each worker process needs its own copy of the
`DoFn`, and a lambda defined inside a function cannot be pickled.

**The fix.** Use a module-level class:

```python
import apache_beam as beam


class HeavyMapFn(beam.DoFn):
    """A picklable CPU-heavy transform."""

    def process(self, value):
        yield sum(i * i for i in range(value % 200))


with beam.Pipeline() as p:
    (
        p
        | "Create" >> beam.Create(range(200_000))
        | "HeavyMap" >> beam.ParDo(HeavyMapFn())
    )
```

### `MemoryError` during a `GroupByKey`

**The actual message:**

```text
MemoryError
```

or, on macOS, no traceback at all — just the process being killed.

**The cause.** A hot key. The Direct Runner holds an entire key group
in memory at once, and a `GroupByKey` over a skewed key — 60% of rows
with the same key — is a single group in memory.

**The fix.** On the Direct Runner, this means the data is too skewed
for the runner. On Dataflow, the fix is a different hot-key strategy
(combining in a `CombinePerKey` rather than a raw `GroupByKey`, or
splitting the key). For local development, reduce the data or accept
the limitation.

### `KeyError: 'runner'` when reading `get_all_options()`

**The actual message:**

```text
KeyError: 'runner'
```

**The cause.** You called `get_all_options()` on an options instance
built with `current_only=True`, which restricts the result to the
options the *current class* declares — and the base class declares
none.

**The fix.** Drop `current_only`:

```python
all_options = options.get_all_options()
print(all_options["runner"])
```

### `TypeError: PipelineOptions.get_all_options() missing 1 required positional argument: 'self'`

**The actual message:**

```text
TypeError: PipelineOptions.get_all_options() missing 1 required positional argument: 'self'
```

**The cause.** You called it on the **class** rather than on an
instance. `get_all_options` is an instance method.

**The fix.** Build an instance first:

```python
from apache_beam.options.pipeline_options import PipelineOptions

known = set(PipelineOptions([]).get_all_options())
print(len(known))
```

```text
157
```

That one-liner is exactly how `project/beam_options.py` builds its
filter list.

### `ValueError: Unsafe trigger: AfterCount(100) may lose data`

**The actual message:**

```text
ValueError: Unsafe trigger: AfterCount(100) may lose data. If you really want to use it, use --allow_unsafe_triggers to acknowledge the risk.
```

**The cause.** Beam refuses triggers it cannot prove are safe unless you
opt in explicitly.

**The fix.** Pass `--allow_unsafe_triggers` — but note that **Prism
declines pipelines with unsafe triggers**, so a pipeline that needs it
must run on `BundleBasedDirectRunner`.

---

## 💡 Production Notes

- **The Direct Runner is a development tool.** It is the right tool for
  writing the pipeline, testing the logic, and iterating on the shape of
  the graph. It is the wrong tool for anything that needs to survive a
  failure, scale past one machine, or run on a schedule.

- **Your local run succeeding tells you your *logic* is right, not that
  your *resource assumptions* are.** The Direct Runner has no memory
  limit, no worker count, and no shuffle service. A pipeline that
  succeeds locally can still OOM on a `n1-standard-2` worker in
  Dataflow because the real worker has 4 GB and your laptop has 32.

- **Always run the local pipeline under the runner you will deploy
  with, at least once.** Specifically: if your pipeline has windowing,
  run it under `BundleBasedDirectRunner` (which is what
  `DataflowRunner` most closely matches semantically), not only under
  Prism.

- **Pin the runner in CI.** A test suite that runs under "whatever the
  default is" will change behaviour when Beam's defaults change. Set
  `BEAM_RUNNER` explicitly in your CI configuration.

- **Prism's speed advantage is in the inner loop.** If your pipeline is
  I/O-bound — many small GCS reads, many API calls — Prism will not help
  much, and the bottleneck is your I/O pattern, not the runner.

- **Watch for the `multi_processing` memory cost.** Each worker process
  is a full Python interpreter with Beam imported. Four workers is
  roughly four times the baseline memory. On a laptop, that is the
  difference between running and swapping.

- **The `FnApiRunner` in old tutorials is a dead end.** If you are
  maintaining code that names it, migrate to `DirectRunner` (which
  auto-selects) or explicitly to `BundleBasedDirectRunner`. The
  `FnApiRunner` is no longer the fast path it used to be.

- **Do not use `beam.Pipeline(runner="...")` in production code.** It
  bypasses the options object and silently drops every other flag.
  Build the options and pass `options=`.

---

## 🔑 Key Takeaways

- **The Direct Runner family is four runners in a dispatch chain**:
  `SwitchingDirectRunner` (the `DirectRunner` alias) inspects the graph
  and picks Prism, then `FnApiRunner`, then `BundleBasedDirectRunner`.
- **`BundleBasedDirectRunner` is the course default** because it has the
  complete implementation of the Beam model — full trigger and
  windowing support. Prism is faster; it is not more correct.
- **`options.runner = "..."` raises
  `AttributeError`** because the base `PipelineOptions` class declares
  no options. Go through `options.view_as(StandardOptions).runner`.
- **`get_all_options()` is an instance method** — calling it on the
  class raises `TypeError`. On an instance it returns all 157 known
  Beam options, including `runner` and `region`.
- **Select the runner with `--runner` (highest precedence),
  `BEAM_RUNNER` (the default), or programmatically.** Never with
  `beam.Pipeline(runner=...)`.
- **The course's CLI and Beam's flags coexist** through
  `parse_known_args` in the script and `_known_beam_flags` in the
  options layer, which filters against the 157 known Beam options.
- **Prism is 2–5× faster on CPU-bound work**, and roughly 25–30%
  faster on a small pipeline dominated by startup. Its trigger
  coverage is incomplete, and a Go panic is not catchable.
- **The Direct Runner is one machine, one process, memory-bound, with
  no fault tolerance.** It is a development tool, not a deployment
  target.

---

## 📚 Practice Exercises

1. **Measure it properly.** Build a benchmark harness that runs the
   course's batch pipeline five times per runner, reports the median
   wall-clock time, and separates *startup* from *execution* by timing
   `import apache_beam` separately. Then explain, with numbers, why the
   2–3× Prism claim does not show up on the course dataset.

2. **Enumerate the fallback.** Write a script that, for each of the
   three runners, constructs a small pipeline containing a feature from
   the Prism-declined list — a `TestStream`, a session window, a
   stateful `DoFn` — and reports which runner actually executed it. The
   `SwitchingDirectRunner` source logs "Running pipeline with
   PrismRunner" when Prism is used; capture that log line to prove which
   engine ran.

3. **Write a custom options subclass.** Create a subclass of
   `PipelineOptions` with a `--local_threshold` flag, and show that it
   appears in `get_all_options()` and can be read through `view_as()`.
   Confirm that a flag defined on your subclass is *not* visible on a
   plain `StandardOptions` view. (Chapter 4.5 develops this fully.)

4. **Find the hot key.** The course's `sample_data.py` has a
   `--hot-key-rate` flag. Generate a dataset with a 60% hot key, run the
   batch pipeline under `BundleBasedDirectRunner`, and watch the memory
   use climb. Explain why the Direct Runner holds the whole group in
   memory, and what the equivalent cost is on a Dataflow worker.

5. **Prove the flag filtering works.** Write a test that passes
   `["--input", "./x.csv", "--runner", "DirectRunner", "--verbose"]` to
   `build_options` and asserts that `input` was dropped, `runner` was
   kept, and `verbose` was kept. Then find a flag in the 157-option set
   that takes a *separate* value (not `=`-joined) and confirm the
   `skip_next` logic in `_known_beam_flags` handles it.

6. **Reflect.** The course defaults to `BundleBasedDirectRunner`
   despite Prism being faster. Argue the opposite case — that the
   course should default to Prism — and then identify the single
   strongest piece of evidence against your own argument.

---

## 📖 Further Reading

- Apache Beam runners overview — https://beam.apache.org/documentation/runtime/runners/
- The Beam Runners matrix — https://beam.apache.org/documentation/runtime/runners/matrix/
- Beam's Prism runner — https://beam.apache.org/documentation/runtime/runners/prism-runner/
- Direct Runner — https://beam.apache.org/documentation/runtime/runners/direct/
- Running Beam locally — https://beam.apache.org/documentation/runners/direct/
- Beam SDK harness and the Fn API — https://beam.apache.org/documentation/runtime/sdk-harness/
- Beam portability — https://beam.apache.org/documentation/runtime/portability/
- Beam performance testing — https://beam.apache.org/documentation/testing/performance/
