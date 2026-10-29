"""
beam_options.py — runner and pipeline-option resolution for the course pipelines.

Every option the pipelines accept is resolved through this module, so there
is exactly one place to look when you wonder "what did `--runner` actually
resolve to?".

The most important default here is the runner: it resolves to
**`DirectRunner`**, not `DataflowRunner`. That means every course command
works with no GCP account, no credentials, and no bill. Asking for
`DataflowRunner` requires an explicit `--runner DataflowRunner` plus a
project, a region, and a staging bucket.

Usage:
    from beam_options import build_options, resolve_runner, is_local

    options = build_options(["--runner", "DirectRunner"])
    print(resolve_runner(options))
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Sequence

log = logging.getLogger(__name__)

try:
    from apache_beam.options.pipeline_options import PipelineOptions

    BEAM_AVAILABLE = True
except ImportError:  # pragma: no cover
    PipelineOptions = None  # type: ignore[assignment,misc]
    BEAM_AVAILABLE = False

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

#: The repository root, five levels up from this file. The course reads
#: configuration from the repo-root `.env` when one exists, so a single
#: checkout can configure every project at once.
REPO_ROOT = Path(__file__).resolve().parents[5]


def load_dotenv(path: Path | None = None, *, override: bool = False) -> dict[str, str]:
    """Load environment variables from a `.env` file.

    The parser handles the common dotenv subset — `KEY=value`, `export
    KEY=value`, comments, and quoted values — without requiring the
    `python-dotenv` package. It is deliberately forgiving: a malformed line
    is logged and skipped rather than crashing the pipeline.

    Args:
        path: The `.env` file to read. Defaults to the repo-root `.env`.
        override: When True, values in the file replace existing environment
            variables. By default, the environment wins.

    Returns:
        The variables that were loaded.
    """
    env_path = path or (REPO_ROOT / ".env")
    if not env_path.is_file():
        return {}

    loaded: dict[str, str] = {}
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        log.warning("could not read %s: %s", env_path, exc)
        return {}

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if not key:
            continue
        loaded[key] = value
        if override or key not in os.environ:
            os.environ[key] = value

    if loaded:
        log.debug("loaded %d variables from %s", len(loaded), env_path)
    return loaded


#: Load the repo-root `.env` at import time, so every module that imports
#: `beam_options` sees the same configuration.
load_dotenv()

#: The default runner.
#:
#: `BundleBasedDirectRunner` is the classic, pure-Python in-process runner.
#: Beam 2.60+ also offers a faster Go runner under the plain name
#: `DirectRunner` (the "Prism" runner), but it does not yet support every
#: trigger and windowing combination — it panics on the `AfterWatermark`
#: trigger that the streaming pipeline uses. The course therefore defaults
#: to the classic runner, and you can still try Prism explicitly with
#: `--runner DirectRunner`.
DEFAULT_RUNNER = os.environ.get("BEAM_RUNNER", "BundleBasedDirectRunner")
DEFAULT_PROJECT = os.environ.get("PROJECT_ID", "")
DEFAULT_REGION = os.environ.get("REGION", "us-central1")
DEFAULT_TEMP_LOCATION = os.environ.get("TEMP_LOCATION", "")
DEFAULT_STAGING_LOCATION = os.environ.get("STAGING_LOCATION", "")
DEFAULT_REGION_SUBNETWORK = os.environ.get("SUBNETWORK", "")
DEFAULT_SERVICE_ACCOUNT = os.environ.get("SERVICE_ACCOUNT_EMAIL", "")

#: Runners that execute locally and therefore need no GCP credentials.
LOCAL_RUNNERS = frozenset(
    {
        "DirectRunner",
        "BundleBasedDirectRunner",
        "FlinkRunner",
        "SparkRunner",
    }
)


# --------------------------------------------------------------------------
# Runner resolution
# --------------------------------------------------------------------------


def resolve_runner(options: Any) -> str:
    """Return the runner name an options object resolves to.

    Args:
        options: A PipelineOptions instance.

    Returns:
        The runner class name, e.g. "DirectRunner" or "DataflowRunner".
    """
    runner = getattr(options, "runner", None)
    if runner is None:
        return DEFAULT_RUNNER
    return getattr(runner, "__name__", str(runner))


def is_local(runner_name: str) -> bool:
    """Check whether a runner executes locally.

    Args:
        runner_name: The runner class name.

    Returns:
        True when the runner does not require GCP credentials.
    """
    return runner_name in LOCAL_RUNNERS


def _known_beam_flags(argv: Sequence[str]) -> list[str]:
    """Filter an argument list down to the flags Beam understands.

    The pipeline scripts accept their own arguments (`--input`, `--output`,
    ...) alongside Beam's (`--runner`, `--job_name`, ...). Beam's
    `PipelineOptions` raises `SystemExit` on a flag it does not know, so
    the pipeline's own flags have to be removed before handing the list
    over.

    Args:
        argv: The raw argument list.

    Returns:
        The subset of `argv` that Beam can parse.
    """
    try:
        from apache_beam.options.pipeline_options import PipelineOptions

        # `get_all_options` is an instance method, so it needs a real
        # options object to enumerate.
        known = set(PipelineOptions([]).get_all_options())
    except Exception:  # pragma: no cover - defensive
        return list(argv)

    filtered: list[str] = []
    skip_next = False
    for arg in argv:
        if skip_next:
            # This is the value of a flag we already dropped.
            skip_next = False
            continue
        if not arg.startswith("--"):
            # A bare value with no preceding flag — keep it, Beam will
            # report it if it really is unexpected.
            filtered.append(arg)
            continue
        name = arg.split("=", 1)[0][2:]
        if name not in known:
            # Not a Beam option. Drop the flag, and its value too when
            # the value was given as a separate argument.
            if "=" not in arg:
                skip_next = True
            continue
        filtered.append(arg)

    return filtered


def build_options(argv: Sequence[str] | None = None) -> Any:
    """Build a PipelineOptions object from command line arguments.

    The runner defaults to `DirectRunner`, and the Dataflow-specific options
    (project, region, staging, temp) are filled in from environment variables
    only when they are actually set. Passing an empty string to Beam is not
    the same as not passing it at all, so unset values are left alone.

    Args:
        argv: Command line arguments. Defaults to `sys.argv[1:]`.

    Returns:
        A configured PipelineOptions instance.

    Raises:
        ImportError: If apache-beam is not installed.
    """
    if not BEAM_AVAILABLE:  # pragma: no cover
        raise ImportError(
            "build_options requires apache-beam. Install it with: "
            "pip install apache-beam[gcp]"
        )

    args = list(argv) if argv is not None else None

    # Default to the local runner when the caller did not choose one.
    if args is None:
        args = []
    args = _known_beam_flags(args)
    if not any(arg == "--runner" or arg.startswith("--runner=") for arg in args):
        args = args + ["--runner", DEFAULT_RUNNER]

    # Beam logs a warning for every flag it cannot parse. The pipeline
    # scripts have their own arguments (`--input`, `--output`, ...), and
    # `_known_beam_flags` has already removed them, so anything still
    # unparseable here is a genuine mistake worth reporting.
    options = PipelineOptions(args)

    # Fill in Dataflow defaults from the environment, but only when the
    # corresponding option is not already set and the value is non-empty.
    #
    # `PipelineOptions` rejects unknown attributes, and the Dataflow-specific
    # options (`region`, `service_account_email`, ...) only exist on the
    # `DataflowOptions` subclass. So each attribute is set on the subclass
    # that actually declares it, and skipped when no subclass does.
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
            # This runner does not support the option. For a local runner
            # that is expected; for Dataflow it means the option was
            # misspelled, which the caller checks for explicitly.
            log.debug("runner does not support option %r", attr)

    return options


def apply_dataflow_defaults(options: Any, *, bucket: str | None = None) -> Any:
    """Fill in the staging and temp locations from a bucket.

    Dataflow requires both locations, and the default locations collide
    between concurrent jobs in the same region. Deriving them from a
    bucket-specific prefix is the simple fix that prevents one job from
    corrupting another's staging area.

    Args:
        options: A PipelineOptions instance.
        bucket: The bucket URI, e.g. "gs://my-bucket". When given, it is
            used to build the staging and temp paths.

    Returns:
        The same options object, modified in place.
    """
    if not bucket:
        return options

    base = bucket.rstrip("/")
    if not getattr(options, "staging_location", None):
        options.staging_location = f"{base}/dataflow/staging"
    if not getattr(options, "temp_location", None):
        options.temp_location = f"{base}/dataflow/temp"
    return options


def pipeline_options_summary(options: Any) -> dict[str, Any]:
    """Summarise the options that matter, for logging and for tests.

    Args:
        options: A PipelineOptions instance.

    Returns:
        A dict of the interesting option values.
    """
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


def describe_environment() -> dict[str, Any]:
    """Describe the local environment for the setup chapter.

    Returns:
        A dict of environment facts.
    """
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
