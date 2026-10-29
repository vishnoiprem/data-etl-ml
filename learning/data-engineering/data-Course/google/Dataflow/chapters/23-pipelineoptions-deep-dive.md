# 4.5 — PipelineOptions Deep Dive

> **Section 4 · GCP Setup & Local Execution · Lecture 4.5 · 6:30**

## 🎯 What you will learn

- The `PipelineOptions` class hierarchy and what each level contributes
- How Beam turns `--flag=value` on `argv` into an attribute
- `view_as()`, and why `options.region` raises but `options.view_as(GoogleCloudOptions).region` works
- The flag families: standard, type, Google Cloud, Dataflow, setup, and the rest
- How to write your own options subclass with `@property` accessors
- Setting options programmatically versus from the command line, and the precedence order
- `get_all_options()` — an instance method, and what happens when you call it on the class
- The course's `describe_environment()` and `pipeline_options_summary()`
- `--save_main_session`, `--experiments`, and the "unparseable argument" warning

---

## 🧠 Concept

### Why options are a class hierarchy

`PipelineOptions` looks like a dataclass with attributes. It is not. It
is an `argparse` wrapper with a **class hierarchy**, and the hierarchy
exists so that a runner can ask for exactly the options it cares about
without knowing about the others.

The shape in Beam 2.77:

```text
PipelineOptions                        (the base — declares no options itself)
├── StandardOptions                    runner, streaming, resource_hints, auto_unique_labels
├── TypeOptions                        type checking, runtime_type_checking, type_hints
├── GoogleCloudOptions                 project, region, job_name, staging/temp, service_account_email
├── SetupOptions                       requirements_file, save_main_session, setup_file
├── DebugOptions                       dump_to, pipeline_options
├── TestOptions                        test_case, ...
├── DirectOptions                      direct_num_workers, direct_running_mode, ...
├── PrismRunnerOptions                 prism_location, prism_log_level, ...
├── WorkerOptions                      environment, ...
├── PortableOptions                    environment_config, ...
└── StreamingOptions, HadoopFileSystemOptions, S3Options, ...
```

Two structural facts explain almost everything people find confusing:

**First, the base class declares no options of its own.** `PipelineOptions`
is an abstract container with the machinery — `__getattr__`,
`__setattr__`, `view_as`, `get_all_options` — and no options. Its
subclasses add options by implementing a single classmethod,
`_add_argparse_args`.

**Second, an instance's attribute access is scoped to its own class.**
`options.region` works only if `region` is declared on
`options.__class__` or one of its ancestors. This is why the *same*
options object raises `AttributeError` for `region` and succeeds for
`runner` — they live on different subclasses.

### How `--flag=value` becomes an attribute

When you construct `PipelineOptions(argv)`, three things happen.

**Step 1 — the parser is built.** `__init__` walks the MRO of
`type(self)` and calls `_add_argparse_args(parser)` on every class
that defines it, stopping at `PipelineOptions`:

```python
for cls in type(self).mro():
    if cls == PipelineOptions:
        break
    elif '_add_argparse_args' in cls.__dict__:
        cls._add_argparse_args(parser)
```

This is why `PipelineOptions([])` knows about `region` even though the
base class does not declare it: the parser is built from the *known
subclasses* registered with Beam, not from the instance's class. Beam
maintains a registry of option classes for exactly this reason.

**Step 2 — `argv` is parsed.** Beam uses its own `_BeamArgumentParser`,
which is an `argparse.ArgumentParser` with `allow_abbrev=False` and a
custom `error` handler. That handler is the source of the
"unparseable argument" behaviour:

```text
WARNING:apache_beam.options.pipeline_options:Discarding unparseable args: ['--input', './sample_data/orders.csv']
```

`parse_known_args` is used, so unknown flags are **collected and
discarded** rather than causing an exit. This is deliberate: Beam
cannot know which flags belong to the user's own tooling, and a hard
failure on an unknown flag would break every script that passes extra
arguments through.

**Step 3 — the values are stored.** The parsed namespace becomes
`self._visible_options`, and `self._all_options` holds the merged
store. `_all_options` is the dict that everything ultimately reads
from, and it is **shared between views**.

The important consequence: **`PipelineOptions` never raises
`SystemExit` on an unknown flag.** It warns and discards. Which means
a typo in a flag name is *silently ignored* — a genuine hazard, and
the reason the course filters the argument list before handing it over
(see `_known_beam_flags` in chapter 4.3).

### `view_as()` and the two accessors

`view_as(cls)` returns a view of the same options object as another
subclass:

```python
def view_as(self, cls):
    view = cls(self._flags)
    for option_name in view._visible_option_list():
        if option_name not in self._all_options:
            self._all_options[option_name] = getattr(view._visible_options, option_name)
    view._all_options = self._all_options
    return view
```

The mechanism: build a new instance of the target class, copy across
any option values the target class declares that are not already
present, and then **share the `_all_options` dict**.

The sharing is the important part, and it is asymmetric in a way that
catches people:

```python
options = PipelineOptions(["--region=us-central1"])
gcp = options.view_as(GoogleCloudOptions)

gcp.region = "europe-west1"

# The shared store saw the change:
options.get_all_options()["region"]     # 'europe-west1'
options.view_as(GoogleCloudOptions).region  # 'europe-west1'

# But the base class still cannot see it:
options.region                          # AttributeError
```

So the rule is:

> **`view_as` gives you access to a subclass's options. It does not give
> the base class access to them. Read and write through the view, or
> use `get_all_options()`.**

The reason `options.region` raises is exactly the reason
`options.runner = "..."` raises (chapter 4.3): the base class's
`_visible_option_list()` is empty, so `__getattr__` and `__setattr__`
both refuse the name.

```python
def __getattr__(self, name):
    if name[:2] == name[-2:] == '__':
        return object.__getattribute__(self, name)
    elif name in self._visible_option_list():
        return self._all_options[name]
    else:
        raise AttributeError(
            "'%s' object has no attribute '%s'" % (type(self).__name__, name))
```

### The flag families

Here is what each family contains, in the terms you will actually use.

| Family | Class | Key flags | What they do |
|---|---|---|---|
| **Standard** | `StandardOptions` | `--runner`, `--streaming`, `--resource_hints`, `--auto_unique_labels`, `--no_wait_until_finish` | Which engine runs the pipeline, and how. `runner` is the one you use constantly. |
| **Type** | `TypeOptions` | `--type_hints`, `--runtime_type_checking`, `--strict_type_hints` | How aggressively Beam type-checks your `DoFn`s. `--type_hints` is how you pass a type hint to a transform. |
| **Google Cloud** | `GoogleCloudOptions` | `--project`, `--region`, `--job_name`, `--staging_location`, `--temp_location`, `--service_account_email`, `--no_auth`, `--template_location`, `--labels` | Everything the Dataflow API needs to submit a job. |
| **Setup** | `SetupOptions` | `--requirements_file`, `--requirements_cache`, `--save_main_session`, `--setup_file` | What gets installed on the workers, and how your session is shipped there. |
| **Debug** | `DebugOptions` | `--dump_to`, `--pipeline_options` | Dump the pipeline graph for offline inspection. |
| **Direct** | `DirectOptions` | `--direct_num_workers`, `--direct_running_mode`, `--direct_runner_bundle_repeat`, `--direct_test_splits` | The local runner's knobs. |
| **Prism** | `PrismRunnerOptions` | `--prism_location`, `--prism_log_level`, `--prism_log_kind` | Where to find the Prism binary and how loudly to log. |
| **Worker** | `WorkerOptions` | `--environment`, `--environment_config` | The worker environment. `--environment=CONTAINER` runs your `DoFn` in a Docker image. |
| **Portable** | `PortableOptions` | `--environment_config`, `--sdk_location` | How to reach a portable runner. |
| **Streaming** | `StreamingOptions` | `--update_compatibility_version` | Version-gated behaviour changes. |
| **Test** | `TestOptions` | `--test_case` | The `TestPipeline` harness. |

Two flags from that table are worth pulling out, because they matter in
practice.

#### `--save_main_session`

```bash
python my_pipeline.py --runner DataflowRunner --save_main_session
```

**The problem it solves.** When Beam submits a Dataflow job, it
serialises your pipeline graph and ships *that* to the workers. It does
not ship your Python interpreter's memory. If your pipeline depends on
something that was created at **import time** in your main script — a
module-level variable, a lookup table loaded from a file, a config
object, a compiled regex with a large pattern list — that state does
not exist on the worker, and the job fails with a `NameError` or an
`AttributeError` that points at a line in your script which obviously
works locally.

**The fix.** `--save_main_session` tells Beam to serialise the
`__main__` module's contents and ship them with the job. It is
necessary in exactly the situations where it is annoying: Colab, Jupyter,
and `python -c` invocations, where the pipeline is defined in a
`__main__` that has no importable module.

**The costs.** It is slower to submit (the whole session is pickled),
the pickle can be large, and **it can fail to pickle** — a common
failure is an unpicklable object (an open socket, a database
connection, a lambda) at module level.

**The better practice** is to not depend on import-time state at all:
put your lookup data in a file and read it inside the `DoFn`, or use a
side input. Then you do not need the flag. But in Colab, you almost
certainly do need it.

#### `--experiments`

```bash
python my_pipeline.py --runner DataflowRunner --experiments=enable_new_shuffle
```

An escape hatch for enabling a feature that is not yet on by default.
It is **Dataflow-specific** and it is **not stable API** — an
experiment can be renamed, have its behaviour changed, or be removed
between releases, with no deprecation period.

The course's `SetupOptions`... no — the `StandardOptions` class
defines it. The flag accepts a comma-separated list and is stored as a
list:

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--experiments=alpha,beta"])
print(options.get_all_options()["experiments"])
```

```text
['alpha', 'beta']
```

**The rules.** Use an experiment only when you have read the
Dataflow release notes for the version you are on. Never let a pipeline
that runs in production depend on one without a comment explaining
which version it was tested against. And always have a plan for
removing it.

### Writing your own options subclass

This is the skill that turns `PipelineOptions` from a mystery into a
tool. The pattern is a class with an `_add_argparse_args` classmethod
that registers your flags, and optionally a property for each one.

```python
from apache_beam.options.pipeline_options import PipelineOptions


class MyOptions(PipelineOptions):
    """Options for the revenue pipeline."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--local_threshold", default=100)
        parser.add_argument("--environment_name", default="dev")

    @property
    def local_threshold(self):
        """The minimum order amount to count locally."""
        return self._all_options["local_threshold"]

    @property
    def environment_name(self):
        """The deployment environment name."""
        return self._all_options["environment_name"]
```

Two details matter.

**The `@property` accessor reads `self._all_options`, not
`self._visible_options`.** This is the pattern Beam's own subclasses
use, and it is what makes the option work when the object is used
through a view. `_all_options` is the shared merged store;
`_visible_options` is the per-instance argparse namespace.

**You do not have to write the properties.** `options.local_threshold`
works without them, because `__getattr__` finds `local_threshold` in
the visible option list. The properties exist to (a) document the
option, (b) give it a type annotation, and (c) survive a rename of
the argparse `dest`.

Using it:

```python
options = MyOptions(["--local_threshold=50"])
print(options.local_threshold)          # 50
print(options.get_all_options()["local_threshold"])  # 50
```

```text
50
50
```

And the isolation property — your option is not visible through an
unrelated view:

```python
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])
standard = options.view_as(StandardOptions)
standard.local_threshold   # AttributeError
```

```text
AttributeError: 'StandardOptions' object has no attribute 'local_threshold'
```

That is the same rule as `region`, and it is the rule that decides
where you must put a flag: **on the subclass that owns it**.

#### The `dest` and the flag name

`argparse` derives the attribute name from the flag name: `--local_threshold`
becomes `local_threshold`. If you want them to differ, set `dest`
explicitly:

```python
parser.add_argument("--local-threshold", dest="local_threshold", default=100)
```

With `dest` set, `--local-threshold` populates `local_threshold`. Without
it, `--local-threshold` would produce the attribute name
`local-threshold`, which is not a valid Python identifier and cannot
be read with dot syntax.

### Setting options: programmatically versus from the command line

There are three sources of option values, and they have a defined
precedence.

**The precedence, highest first:**

1. **Keyword arguments to the constructor.** These override the flags:

```python
options = PipelineOptions(["--region=us-east1"], region="us-west1")
print(options.get_all_options()["region"])   # us-west1
```

2. **Command-line flags.** Parsed from `argv`.

3. **The constructor's default.** From the `parser.add_argument` default.

And there is a fourth source that sits *outside* Beam, and it is the
one the course uses: **the environment**. The course's `build_options`
reads `PROJECT_ID`, `REGION`, `TEMP_LOCATION`, `STAGING_LOCATION`, and
`SERVICE_ACCOUNT_EMAIL` from the environment and applies them **only
when the option is not already set**:

```python
for attr, env_value in (
    ("project", DEFAULT_PROJECT),
    ("region", DEFAULT_REGION),
    ("temp_location", DEFAULT_TEMP_LOCATION),
    ("staging_location", DEFAULT_STAGING_LOCATION),
    ("service_account_email", DEFAULT_SERVICE_ACCOUNT),
):
    if not env_value:
        continue
    if getattr(options, attr, None) not in (None, ""):
        continue
    try:
        setattr(options, attr, env_value)
    except AttributeError:
        log.debug("runner does not support option %r", attr)
```

Read that loop carefully, because it encodes two important decisions:

**The `not in (None, "")` guard.** An empty string is *not* the same as
unset. Beam's `GoogleCloudOptions` defaults `region` to `None`, but
some options default to `""`. If you blindly set an option to an
empty string, you are telling the runner "use the empty path", which
produces a confusing failure much later. The guard makes "unset" mean
"not configured".

**The `try`/`except AttributeError`.** `project` and `region` live on
`GoogleCloudOptions`, not on the base class. Setting them on a local
runner's options object raises `AttributeError`. The course catches
it, because for a local runner the absence of those options is
expected, not an error.

Then, in `batch_pipeline.py`, explicit command-line values are applied
*on top* of the options object, which is why `--project` on the command
line beats `PROJECT_ID` in the environment:

```python
for attr, value in (
    ("project", args.project),
    ("region", args.region),
    ...
):
    if not value:
        continue
    try:
        setattr(options, attr, value)
    except AttributeError:
        log.warning("this runner does not support the --%s option", ...)
```

**The complete precedence, in the course:**

```text
explicit --project on the command line
        ↓ beats
PROJECT_ID in the environment
        ↓ beats
the argparse default (None)
```

**The right way to set an option programmatically** is through the
constructor's keyword arguments, because they participate in Beam's own
precedence rules:

```python
options = PipelineOptions(["--runner=DataflowRunner"], project="my-project")
```

Not this:

```python
options = PipelineOptions(["--runner=DataflowRunner"])
options.project = "my-project"   # AttributeError on a base PipelineOptions
```

### `get_all_options()` — the instance method

This is the API that unlocks programmatic access to everything, and it
has one sharp edge.

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])
all_options = options.get_all_options()
```

It returns a **dict** of every known option and its current value.
In Beam 2.77 that is 157 options for a base `PipelineOptions`, and 159
once you add a two-flag custom subclass.

**The sharp edge: it is an instance method.**

```python
from apache_beam.options.pipeline_options import PipelineOptions

PipelineOptions.get_all_options()
```

```text
TypeError: PipelineOptions.get_all_options() missing 1 required positional argument: 'self'
```

An unbound method needs an instance. The fix is to build a throwaway
instance — which is exactly what the course's `_known_beam_flags` does,
because it needs the *names* of all options, not their values:

```python
known = set(PipelineOptions([]).get_all_options())
```

**The parameters are worth knowing:**

| Parameter | Default | Effect |
|---|---|---|
| `drop_default` | `False` | Omit options whose value equals their default. Useful for a compact diff. |
| `add_extra_args_fn` | `None` | A callback to add runner-specific flags to the parser before parsing. |
| `retain_unknown_options` | `False` | Keep flags that no known options class declared, instead of discarding them. |
| `display_warnings` | `False` | Print the "discarding unparseable args" warning. |
| `current_only` | `False` | Restrict the result to the options the *current class* declares. This is the flag that causes `KeyError: 'runner'`. |

### The course's helpers

Two functions in `project/beam_options.py` (and their twins in
`resources/beam_client.py`) are worth reading, because they are the
practical answer to "what will actually happen when I run this?".

**`describe_environment()`** — the setup summary:

```python
import os
from typing import Any

DEFAULT_PROJECT = os.environ.get("PROJECT_ID", "")
DEFAULT_REGION = os.environ.get("REGION", "us-central1")
DEFAULT_TEMP_LOCATION = os.environ.get("TEMP_LOCATION", "")
DEFAULT_STAGING_LOCATION = os.environ.get("STAGING_LOCATION", "")
DEFAULT_SERVICE_ACCOUNT = os.environ.get("SERVICE_ACCOUNT_EMAIL", "")


def describe_environment() -> dict[str, Any]:
    """Describe the local environment for the setup chapter."""
    import sys

    try:
        import apache_beam
        beam_version = apache_beam.__version__
    except ImportError:
        beam_version = None

    return {
        "python_version": sys.version.split()[0],
        "beam_version": beam_version,
        "project": DEFAULT_PROJECT or "(not set)",
        "region": DEFAULT_REGION,
        "temp_location": DEFAULT_TEMP_LOCATION or "(not set)",
        "staging_location": DEFAULT_STAGING_LOCATION or "(not set)",
        "service_account": DEFAULT_SERVICE_ACCOUNT or "(not set)",
    }
```

It answers the question every debugging session starts with: *which
Beam, which Python, which project?* Note the `or "(not set)"` pattern
— it makes an unset value visible rather than indistinguishable from an
empty one.

**`pipeline_options_summary(options)`** — the per-run summary:

```python
from typing import Any


def resolve_runner(options: Any) -> str:
    """Return the runner name an options object resolves to."""
    runner = getattr(options, "runner", None)
    if runner is None:
        return DEFAULT_RUNNER
    return getattr(runner, "__name__", str(runner))


def is_local(runner_name: str) -> bool:
    """Check whether a runner executes locally."""
    return runner_name in LOCAL_RUNNERS


def pipeline_options_summary(options: Any) -> dict[str, Any]:
    """Summarise the options that matter, for logging and for tests."""
    runner = resolve_runner(options)
    return {
        "runner": runner,
        "is_local": is_local(runner),
        "project": getattr(options, "project", None),
        "region": getattr(options, "region", None),
        "staging_location": getattr(options, "staging_location", None),
        "temp_location": getattr(options, "temp_location", None),
        "streaming": bool(getattr(options, "streaming", False)),
    }
```

Two techniques in this function are worth stealing:

**`getattr(options, "project", None)` instead of `options.project`.**
The three-argument `getattr` swallows the `AttributeError` and returns
the default. This is how the course reads an option that may not exist
on the current subclass — a `GoogleCloudOptions` option, read from a
local runner's options object.

**`resolve_runner(options)` normalises the runner to a string.** The
`runner` option holds whatever was parsed; `resolve_runner` turns it
into a comparable class name, and `is_local()` then answers the only
question that matters: *does this run need cloud credentials?*

```python
def resolve_runner(options: Any) -> str:
    runner = getattr(options, "runner", None)
    if runner is None:
        return DEFAULT_RUNNER
    return getattr(runner, "__name__", str(runner))
```

Note the `getattr(runner, "__name__", str(runner))` — it handles both
a class (which has `__name__`) and a plain string (which does not).

### The "unparseable argument" warning

You have seen this. It looks alarming and it is usually harmless — but
"usually" is doing real work in that sentence.

```text
WARNING:apache_beam.options.pipeline_options:Discarding unparseable args: ['--input', './sample_data/orders.csv']
```

**The cause.** A flag that no registered options class declares was
passed to `PipelineOptions`. In the course's case, that is by design:
`--input` and `--output` belong to the *script*, not to Beam, and
`batch_pipeline.py` passes its raw `argv` straight through to
`build_options`.

**Why it is not always harmless.** The word is **"discarding"**. The
flag is dropped, not just ignored. If the flag was supposed to reach
your pipeline and it did not, your pipeline ran with a *default* value
instead of the one you typed. The most common instance of this: you
add `--input` to the Beam options by mistake, the warning scrolls by,
and the pipeline reads the default path while you believe it read
yours.

**The rule.** If a flag you *intended* for Beam shows up in the
discarded list, something upstream filtered it incorrectly. If a flag
you intended for your *script* shows up, that is the expected
behaviour of a script that passes raw `argv` to Beam.

**How to silence it legitimately.** Two options:

```python
# Option A: turn the warning off for a call
options = PipelineOptions(argv, display_warnings=False)

# Option B: keep the flags Beam understands
known = set(PipelineOptions([]).get_all_options())
filtered = [arg for arg in argv if arg.split("=", 1)[0][2:] in known]
options = PipelineOptions(filtered)
```

The course uses option B, in `_known_beam_flags`, and it is the better
one — it also prevents the "silently discarded flag" hazard, because
flags that survive the filter are ones Beam genuinely understands.

---

## 🛠️ Hands-On

### Part 1 — Map the hierarchy

Start by seeing the class hierarchy and what each level contributes:

```python
from apache_beam.options import pipeline_options as po

FAMILIES = (
    "StandardOptions",
    "TypeOptions",
    "GoogleCloudOptions",
    "SetupOptions",
    "DebugOptions",
    "DirectOptions",
    "PrismRunnerOptions",
    "WorkerOptions",
    "PortableOptions",
    "StreamingOptions",
    "TestOptions",
)

for name in FAMILIES:
    cls = getattr(po, name)
    print(f"{name:24} {cls.__mro__[1].__name__}")
```

```text
StandardOptions           PipelineOptions
TypeOptions               PipelineOptions
GoogleCloudOptions        PipelineOptions
SetupOptions              PipelineOptions
DebugOptions              PipelineOptions
DirectOptions             PipelineOptions
PrismRunnerOptions        PipelineOptions
WorkerOptions             PipelineOptions
PortableOptions           PipelineOptions
StreamingOptions          PipelineOptions
TestOptions               PipelineOptions
```

Every family is a *sibling* of `PipelineOptions`, not a subclass of one
another. That is why a single options object has to be viewed as
several of them.

Now see which options each family declares, by counting the visible
options on a view of each:

```python
from apache_beam.options import pipeline_options as po
from apache_beam.options.pipeline_options import PipelineOptions

base = PipelineOptions([])

for name in ("StandardOptions", "TypeOptions", "GoogleCloudOptions",
             "SetupOptions", "DirectOptions"):
    cls = getattr(po, name)
    view = base.view_as(cls)
    visible = view._visible_option_list()
    print(f"{name:22} {len(visible):3} options")
```

```text
StandardOptions          5 options
TypeOptions             10 options
GoogleCloudOptions     26 options
SetupOptions            17 options
DirectOptions            6 options
```

The counts are larger than the number of flags each family *declares*,
because `_visible_option_list()` includes the options a family
inherits through `PipelineOptions` — and `PipelineOptions` itself
pulls in `StandardOptions`' flags as part of building the parser. The
`GoogleCloudOptions` view, for instance, sees `runner` and `streaming`
as well as its own `project`, `region`, and `job_name`.

That is exactly why `get_all_options()` — which merges the *entire*
registry — returns 157, and why a base instance's visible list is
empty.

### Part 2 — Prove the two accessors

This is the mechanic the chapter is built around:

```python
from apache_beam.options.pipeline_options import (
    GoogleCloudOptions,
    PipelineOptions,
    StandardOptions,
)

options = PipelineOptions(["--runner=BundleBasedDirectRunner", "--region=us-central1"])

# The base class can see NOTHING.
for attribute in ("runner", "region", "project"):
    try:
        getattr(options, attribute)
        print(f"options.{attribute:10} -> OK")
    except AttributeError as exc:
        print(f"options.{attribute:10} -> {exc}")
```

```text
options.runner     -> 'PipelineOptions' object has no attribute 'runner'
options.region    -> 'PipelineOptions' object has no attribute 'region'
options.project   -> 'PipelineOptions' object has no attribute 'project'
```

Now the views:

```python
from apache_beam.options.pipeline_options import (
    GoogleCloudOptions,
    PipelineOptions,
    StandardOptions,
)

options = PipelineOptions(["--runner=BundleBasedDirectRunner", "--region=us-central1"])

print("standard.view runner:", options.view_as(StandardOptions).runner)
print("gcp.view region     :", options.view_as(GoogleCloudOptions).region)
```

```text
standard.view runner: BundleBasedDirectRunner
gcp.view region     : us-central1
```

And the shared store — the part that makes views useful:

```python
from apache_beam.options.pipeline_options import (
    GoogleCloudOptions,
    PipelineOptions,
    StandardOptions,
)

options = PipelineOptions(["--region=us-central1"])
gcp = options.view_as(GoogleCloudOptions)

gcp.region = "europe-west1"

print("merged store    :", options.get_all_options()["region"])
print("fresh view      :", options.view_as(GoogleCloudOptions).region)
print("base still blind:", end=" ")
try:
    options.region
except AttributeError:
    print("AttributeError")
```

```text
merged store    : europe-west1
fresh view      : europe-west1
base still blind: AttributeError
```

### Part 3 — Enumerate every option Beam knows

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])
all_options = options.get_all_options()

print("total options:", len(all_options))

# The ones you actually use
for name in ("runner", "streaming", "project", "region", "job_name",
             "staging_location", "temp_location", "service_account_email",
             "requirements_file", "save_main_session", "experiments",
             "direct_num_workers", "direct_running_mode"):
    print(f"  {name:22} {all_options.get(name)!r}")
```

```text
total options: 157
  runner                 'BundleBasedDirectRunner'
  streaming              False
  project                None
  region                 None
  job_name               None
  staging_location       None
  temp_location          None
  service_account_email  None
  requirements_file      None
  save_main_session      None
  experiments            None
  direct_num_workers     1
  direct_running_mode    'in_memory'
```

Now the instance-method trap:

```python
from apache_beam.options.pipeline_options import PipelineOptions

try:
    PipelineOptions.get_all_options()
except TypeError as exc:
    print("TypeError:", exc)
```

```text
TypeError: PipelineOptions.get_all_options() missing 1 required positional argument: 'self'
```

And the `current_only` variant that causes a `KeyError`:

```python
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(["--runner=BundleBasedDirectRunner"])

try:
    options.get_all_options(current_only=True)["runner"]
except KeyError as exc:
    print("KeyError:", exc)
```

```text
KeyError: 'runner'
```

`current_only=True` restricts the result to the options the *base
class* declares — and the base class declares none.

### Part 4 — Build your own options subclass

This is the main deliverable. Save it as `project/course_options.py`:

```python
"""course_options.py — a custom PipelineOptions subclass for the course.

This shows the full pattern:

  * a classmethod that registers the flags
  * @property accessors that read the shared `_all_options` store
  * a `describe()` helper for logging
"""
from __future__ import annotations

from apache_beam.options.pipeline_options import PipelineOptions


class CourseOptions(PipelineOptions):
    """Options for the course pipelines.

    Attributes:
        local_threshold: Minimum order amount, in EUR, to count as revenue.
        environment_name: A label for the deployment environment.
        write_to_gcs: Whether the output prefix is a gs:// URI.
    """

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            "--local_threshold",
            type=float,
            default=0.0,
            help="Minimum order amount in EUR to count toward revenue.",
        )
        parser.add_argument(
            "--environment_name",
            default="local",
            help="A label for the deployment environment.",
        )
        parser.add_argument(
            "--write_to_gcs",
            action="store_true",
            default=False,
            help="Whether the output path is a gs:// URI.",
        )

    @property
    def local_threshold(self) -> float:
        """The minimum order amount to count toward revenue."""
        return self._all_options["local_threshold"]

    @property
    def environment_name(self) -> str:
        """The deployment environment label."""
        return self._all_options["environment_name"]

    @property
    def write_to_gcs(self) -> bool:
        """Whether the output path is a gs:// URI."""
        return self._all_options["write_to_gcs"]

    def describe(self) -> dict[str, object]:
        """Summarise this options object for logging."""
        return {
            "environment_name": self.environment_name,
            "local_threshold": self.local_threshold,
            "write_to_gcs": self.write_to_gcs,
        }
```

Now exercise it:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

from course_options import CourseOptions

options = CourseOptions(
    ["--local_threshold=50.0", "--environment_name=staging", "--write_to_gcs"]
)

print("threshold :", options.local_threshold)
print("environment:", options.environment_name)
print("to gcs    :", options.write_to_gcs)
print("describe  :", options.describe())

# The option count grew by three
print("total options:", len(options.get_all_options()))
```

```text
threshold : 50.0
environment: staging
to gcs    : True
describe  : {'environment_name': 'staging', 'local_threshold': 50.0, 'write_to_gcs': True}
total options: 160
```

157 base options plus your three.

Now the isolation property — your options are not visible through an
unrelated view:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

from apache_beam.options.pipeline_options import StandardOptions
from course_options import CourseOptions

options = CourseOptions(["--local_threshold=50.0"])
standard = options.view_as(StandardOptions)

print("standard view runner:", standard.runner)
try:
    standard.local_threshold
except AttributeError as exc:
    print("standard.local_threshold ->", exc)
```

```text
standard view runner: None
standard.local_threshold -> 'StandardOptions' object has no attribute 'local_threshold'
```

Note that `runner` is `None` here: `CourseOptions` was constructed
without a `--runner` flag, so the option was never set. It is visible
through the view (the view declares it) but it holds `None`.

### Part 5 — Use the custom options in a pipeline

A custom options subclass works exactly like the built-in ones:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

import apache_beam as beam
from apache_beam.io.textio import ReadFromText, WriteToText

from course_options import CourseOptions

options = CourseOptions(["--local_threshold=50.0"])

INPUT = "./sample_data/orders.csv"
OUTPUT = "./out/options_demo"

with beam.Pipeline(options=options) as p:
    (
        p
        | "ReadOrders" >> ReadFromText(INPUT, skip_header_lines=1)
        | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        | "KeyByRegion" >> beam.Map(lambda row: (row[3], float(row[7])))
        | "SumRevenue" >> beam.CombinePerKey(sum)
        | "FormatRows" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
        | "WriteSummary" >> WriteToText(OUTPUT, num_shards=1)
    )
```

Note that the pipeline receives `options=options`, and Beam resolves
the runner from it — `CourseOptions` inherits the `runner` option
because the base `PipelineOptions` parser includes `StandardOptions`.

Verify:

```bash
cat out/options_demo*
```

```text
APAC,589517.07
AMER,608044.31
EMEA,605463.21
LATAM,593813.37
```

### Part 6 — Test the precedence order

```python
from apache_beam.options.pipeline_options import PipelineOptions

# 1. Constructor kwargs beat the flags
options = PipelineOptions(["--region=us-east1"], region="us-west1")
print("kwargs beat flags:", options.get_all_options()["region"])

# 2. The flag beats the default
options = PipelineOptions(["--region=us-east1"])
print("flag beats default:", options.get_all_options()["region"])

# 3. The default wins when nothing is passed
options = PipelineOptions([])
print("default          :", options.get_all_options()["region"])
```

```text
kwargs beat flags: us-west1
flag beats default: us-east1
default          : None
```

And the course's environmental layer on top:

```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

os.environ["PROJECT_ID"] = "env-project"

from beam_options import build_options

# The environment fills in a value the flag did not set
options = build_options(["--region=europe-west1"])
print("region  :", options.get_all_options()["region"])
print("project :", options.get_all_options()["project"])
```

```text
region  : europe-west1
project : env-project
```

### Part 7 — Reproduce the "unparseable argument" warning

```python
from apache_beam.options.pipeline_options import PipelineOptions

# A flag that belongs to the course's script, not to Beam
options = PipelineOptions(["--input", "./sample_data/orders.csv"])
print("input survived:", "input" in options.get_all_options())
```

```text
WARNING:apache_beam.options.pipeline_options:Discarding unparseable args: ['--input', './sample_data/orders.csv']
input survived: False
```

**The flag was discarded, not just ignored.** That is the hazard. Now
see how the course prevents it, by filtering first:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("project").resolve()))

from beam_options import _known_beam_flags

argv = [
    "--input", "./sample_data/orders.csv",
    "--runner", "DirectRunner",
    "--verbose",
]
filtered = _known_beam_flags(argv)

print("before:", argv)
print("after :", filtered)
```

```text
before: ['--input', './sample_data/orders.csv', '--runner', 'DirectRunner', '--verbose']
after : ['--runner', 'DirectRunner']
```

`--input` and its value are gone — it is the course script's flag, not
Beam's. `--runner` and its value survive, because Beam knows it.
`--verbose` is also gone, and that is correct too: `--verbose` is the
course script's own flag (it controls `logging.basicConfig`), not a
Beam option. No warning is printed, because everything that reaches
Beam is something Beam genuinely understands.

---

## 🛠️ Common Errors and Fixes

### `AttributeError: 'PipelineOptions' object has no attribute 'region'`

**The actual message:**

```text
AttributeError: 'PipelineOptions' object has no attribute 'region'
```

**The cause.** You read a `GoogleCloudOptions` attribute from a base
`PipelineOptions` instance. The base class declares no options, so
`__getattr__` refuses.

**The fix.** Go through the view:

```python
from apache_beam.options.pipeline_options import GoogleCloudOptions, PipelineOptions

options = PipelineOptions(["--region=us-central1"])
region = options.view_as(GoogleCloudOptions).region
print(region)
```

Or, more robustly, use `getattr` with a default:

```python
region = getattr(options, "region", None)
```

### `AttributeError: 'StandardOptions' object has no attribute 'job_name'`

**The actual message:**

```text
AttributeError: 'StandardOptions' object has no attribute 'job_name'
```

**The cause.** `job_name` is declared on `GoogleCloudOptions`, not on
`StandardOptions`. A view only sees the options its own class declares.

**The fix.**

```python
from apache_beam.options.pipeline_options import GoogleCloudOptions, PipelineOptions

options = PipelineOptions(["--job_name=nightly-revenue"])
job_name = options.view_as(GoogleCloudOptions).job_name
print(job_name)
```

### `TypeError: PipelineOptions.get_all_options() missing 1 required positional argument: 'self'`

**The actual message:**

```text
TypeError: PipelineOptions.get_all_options() missing 1 required positional argument: 'self'
```

**The cause.** You called an instance method on the class.

**The fix.** Build an instance:

```python
known = set(PipelineOptions([]).get_all_options())
```

### `KeyError: 'runner'`

**The actual message:**

```text
KeyError: 'runner'
```

**The cause.** You called `get_all_options(current_only=True)` on a
base `PipelineOptions` instance. The base class declares no options, so
the result is empty.

**The fix.** Drop `current_only`:

```python
options.get_all_options()["runner"]
```

### `WARNING:apache.beam.options.pipeline_options:Discarding unparseable args: ['--input', ...]`

**The actual message:**

```text
WARNING:apache.beam.options.pipeline_options:Discarding unparseable args: ['--input', './sample_data/orders.csv']
```

**The cause.** A flag that no options class declares reached
`PipelineOptions`.

**The fix.** If the flag is meant for your own script, filter it out
before handing the argument list to Beam:

```python
known = set(PipelineOptions([]).get_all_options())
filtered = [a for a in argv if a.split("=", 1)[0][2:] in known]
options = PipelineOptions(filtered)
```

If the flag is *meant* for Beam and it is being discarded, something
upstream is filtering incorrectly — check the `dest` name against
`get_all_options()`.

### `ValueError: Invalid --type-hints value`

**The actual message:**

```text
ValueError: Invalid --type-hints value. Please specify a string in the form of "<module>.<callable>". For example: "apache_beam.transforms.Map.__init__".
```

**The cause.** The `--type_hints` flag expects a fully-qualified
callable path, not a bare name.

**The fix.**

```bash
--type_hints="apache_beam.transforms.Map.__init__"
```

### `NameError: name 'lookup_table' is not defined` on a Dataflow worker

**The actual message:**

```text
NameError: name 'lookup_table' is not defined
```

**The cause.** Your pipeline depends on a module-level variable that
was created at import time in `__main__`. The worker receives the
*pipeline graph*, not your interpreter's memory, so the variable does
not exist there.

**The fix — two options.**

The quick fix, for Colab and notebooks:

```bash
--save_main_session
```

The correct fix — remove the dependency on import-time state. Read the
data inside the `DoFn`, or pass it as a side input:

```python
beam.Map(process_order, reference=beam.pvalue.AsDict(reference))
```

### `AttributeError: 'CourseOptions' object has no attribute 'local_threshold'` after adding a property

**The actual message:**

```text
AttributeError: 'CourseOptions' object has no attribute 'local_threshold'
```

**The cause.** You wrote a `@property` that reads `self._all_options["local_threshold"]`,
but the flag's argparse `dest` does not match the key. A flag named
`--local-threshold` produces the key `local-threshold`, not
`local_threshold`.

**The fix.** Set the `dest` explicitly:

```python
parser.add_argument("--local-threshold", dest="local_threshold", default=100)
```

Or name the flag with underscores: `--local_threshold`.

### `AssertionError: Transform name is already used`

**The actual message:**

```text
RuntimeError: Transform name is already used: KeyByRegion
```

**The cause.** Two transforms in the same pipeline share a label.

**The fix.** Make the labels unique within the pipeline. The course
linter catches this statically:

```bash
python resources/audit_course.py
```

### `TypeError: unhashable type: 'dict'` when setting a pipeline option

**The actual message:**

```text
TypeError: unhashable type: 'dict'
```

**The cause.** You assigned a dict to an option whose value is expected
to be a scalar, and Beam tried to use it as a dict key in `_all_options`.

**The fix.** Store the dict in a JSON string, or use a different
option. Beam's options are flat by design.

---

## 💡 Production Notes

- **Put your flags on the subclass that owns them.** A custom
  `PipelineOptions` subclass is the right home for anything specific
  to your pipeline. It documents itself, it is discoverable with
  `--help`, and it keeps you from inventing a parallel mechanism for
  configuration.

- **Log the resolved options, not the intended ones.** The course
  logs `pipeline_options_summary(options)` before every run. When a
  job behaves unexpectedly, the first question is always "what did the
  runner actually get", and this line answers it.

- **The environment is a good default; the command line is a good
  override.** The course's order — command line beats environment
  beats default — is the one to copy. It lets a CI system set
  `PROJECT_ID` once and still let a developer override it for one run.

- **Never pass an empty string where "unset" is meant.** `""` is a
  value, and Beam will use it. The `not in (None, "")` guard in
  `build_options` exists for exactly this.

- **Treat an "unparseable args" warning as a possible bug, not noise.**
  A discarded flag is a flag that did not arrive. If the pipeline used
  a default when you expected your value, that warning is the reason.

- **Keep `--experiments` off the critical path.** Experiments change
  behaviour without notice and are removed without deprecation. If a
  production job depends on one, comment the flag with the SDK version
  it was verified against, and put removing it on the roadmap.

- **`--save_main_session` is a Colab tool, not a design.** If your
  pipeline needs it, that is a signal that it depends on import-time
  state, which is a smell. Use side inputs.

- **Pin the Beam version in CI.** The option set changes between
  releases — 157 options in 2.77 — and a script that depends on an
  option's default will change behaviour when you upgrade. Assert the
  option values you care about in a test rather than trusting the
  defaults.

---

## 🔑 Key Takeaways

- **`PipelineOptions` is an argparse wrapper with a class hierarchy.**
  The base class declares *no* options; each subclass registers its
  own through `_add_argparse_args`.
- **Attribute access is scoped to the instance's own class.** That is
  why `options.region` raises and
  `options.view_as(GoogleCloudOptions).region` works.
- **`view_as` shares the `_all_options` store** between views, so
  writing through one view is visible to other views — but the base
  class still cannot see it.
- **Unknown flags are *discarded*, not just ignored**, with a
  `WARNING:...Discarding unparseable args` message. A flag you meant
  for Beam that lands in that list is a flag that did not arrive.
- **Precedence, highest first:** constructor kwargs → command-line
  flags → environment variables → argparse defaults.
- **`get_all_options()` is an instance method** — 157 options in
  Beam 2.77. Calling it on the class raises `TypeError`;
  `current_only=True` on a base instance returns an empty dict.
- **Your own options subclass** needs an `_add_argparse_args`
  classmethod and `@property` accessors that read `self._all_options`.
- **`--save_main_session` is for Colab**, and it is a symptom of
  depending on import-time state. `--experiments` is unstable API.

---

## 📚 Practice Exercises

1. **Build a production options class.** Write a `CourseOptions`
   subclass with at least four flags: `--local_threshold`,
   `--environment_name`, `--write_to_gcs`, and one of your own. Add
   `@property` accessors, a `describe()` method, and a `validate()`
   method that raises `ValueError` when the combination is invalid
   (for example, `--write_to_gcs` set but no `BUCKET` in the
   environment). Then write a pytest that constructs it with each
   invalid combination and asserts the error.

2. **Enumerate and diff the option set.** Write a script that captures
   `sorted(PipelineOptions([]).get_all_options())` and saves it to a
   JSON file. Run it under two different Beam versions (in two virtual
   environments) and diff the two lists. Explain which options were
   added, which were removed, and which of the changes would silently
   alter the behaviour of an existing pipeline.

3. **Prove the "silently discarded" hazard.** Write a pipeline that
   reads its input path from an option. Add the option to a custom
   subclass, then deliberately filter it out with `_known_beam_flags`
   (or with a bad `dest`), and show that the pipeline runs against the
   *default* path rather than failing. Then show how you would make
   that failure loud instead of silent.

4. **Trace the precedence end to end.** With `PROJECT_ID` set in the
   environment, run the batch pipeline with `--project` on the command
   line, then without it, and capture the `pipeline options:` log line
   in each case. Explain every difference in terms of the precedence
   rules in this chapter, and identify the line of `build_options`
   responsible for each.

5. **Audit a codebase for option hygiene.** Write a script that greps
   a Python project for patterns that suggest option misuse:
   `options.<google_cloud_option>` without a `view_as`,
   `getattr(options, ...)` where a direct attribute would do,
   `PipelineOptions.get_all_options()` called on the class rather than
   an instance, and any assignment to `options.runner`. Report each
   occurrence with the file and line.

6. **Reflect.** This chapter says the base class declares no options,
   and that a view only sees what its own class declares. Beam's
   `Pipeline.__init__` still resolves the runner from
   `options.view_as(StandardOptions).runner`. Given that, explain why
   Beam chose this design over a flat namespace of 157 attributes, and
   what would break if they had.

---

## 📖 Further Reading

- Beam's PipelineOptions — https://beam.apache.org/documentation/programming-guide/#options
- Beam SDK developer guide: setting pipeline options — https://beam.apache.org/documentation/programming-guide/
- Beam's `pipeline_options.py` source — https://github.com/apache/beam/blob/master/sdk/python/apache_beam/options/pipeline_options.py
- Beam's DataflowOptions and the full flag list — https://beam.apache.org/documentation/programming-guide/#dataflowoptions
- Cloud Dataflow pipeline options — https://cloud.google.com/dataflow/docs/guides/specifying-runtime-environments
- Beam in Colab — https://beam.apache.org/getting-started/#colab
- Beam's `--save_main_session` and worker setup — https://beam.apache.org/documentation/deployment/environment/
- Beam portability: the SDK harness and options — https://beam.apache.org/documentation/runtime/sdk-harness/
