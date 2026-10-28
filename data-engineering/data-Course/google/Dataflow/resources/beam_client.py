#!/usr/bin/env python3
"""Shared helpers for the Dataflow course.

Everything in here is deliberately importable without a GCP account, so a
notebook can be read and executed on a laptop with no credentials at all.

The helpers fall into three groups:

* **Environment discovery** — `describe_environment`, `load_dotenv`. These
  tell a reader what the pipeline is actually going to do before it does
  it, which is the difference between "it worked" and "I know why it
  worked".
* **Option resolution** — `build_options`, `resolve_runner`. Beam's
  `PipelineOptions` hierarchy is deep and its flags are not discoverable
  from the constructor; these helpers wrap it so the course code reads
  clearly.
* **Job submission** — `submit_dataflow_job`, `describe_job`. Thin
  wrappers over `gcloud dataflow jobs` that return structured data
  instead of raw shell output.

Usage:
    python resources/beam_client.py
    python resources/beam_client.py --runner DataflowRunner
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

#: The repository root — five levels up from `resources/`.
REPO_ROOT = Path(__file__).resolve().parents[5]

#: Runners that need no cloud credentials. `BundleBasedDirectRunner` is
#: the classic pure-Python runner; `DirectRunner` is the newer Go-based
#: Prism runner.
LOCAL_RUNNERS = frozenset(
    {
        "DirectRunner",
        "BundleBasedDirectRunner",
        "FnApiRunner",
        "PortableRunner",
        "FlinkRunner",
        "SparkRunner",
    }
)

#: Runners that submit a job to a managed service.
CLOUD_RUNNERS = frozenset(
    {
        "DataflowRunner",
        "SparkRunner",
        "FlinkRunner",
        "PrismRunner",
    }
)

#: The runner the course defaults to. `BundleBasedDirectRunner` supports
#: the full trigger and windowing feature set; the Prism `DirectRunner`
#: does not yet support `AfterWatermark` or `+inf` watermark evaluation.
DEFAULT_RUNNER = os.environ.get("BEAM_RUNNER", "BundleBasedDirectRunner")


# --------------------------------------------------------------------------
# Environment discovery
# --------------------------------------------------------------------------


def load_dotenv(path: str | os.PathLike[str] | None = None, *, override: bool = False) -> dict[str, str]:
    """Load environment variables from a `.env` file.

    The file is read from the repository root by default. A missing file
    is not an error — most readers will not have one, and the course is
    designed to run without any configuration at all.

    Args:
        path: The `.env` file to read. Defaults to `<repo root>/.env`.
        override: When True, values in the file replace variables that are
            already set in the environment. When False (the default) the
            environment wins, which is the conventional precedence.

    Returns:
        A dict of the variables that were loaded.
    """
    env_path = Path(path) if path else REPO_ROOT / ".env"
    loaded: dict[str, str] = {}

    if not env_path.is_file():
        # A `.env` *directory* is a virtualenv, not a dotenv file. Several
        # repos in this family use `.env` for the venv, so treat it as
        # "no configuration" rather than crashing.
        log.debug("no dotenv file at %s — continuing with the environment", env_path)
        return loaded

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        loaded[key] = value
        if override or key not in os.environ:
            os.environ[key] = value

    log.debug("loaded %d variables from %s", len(loaded), env_path)
    return loaded


def has_gcloud() -> bool:
    """Return True when the `gcloud` CLI is on the PATH."""
    return shutil.which("gcloud") is not None


def describe_environment() -> dict[str, Any]:
    """Summarise the environment a pipeline would run in.

    This is the first thing to print when a job does not behave as
    expected. Most "the pipeline is broken" reports are really "the
    pipeline ran on the wrong runner with the wrong project" reports.

    Returns:
        A dict describing the Python, Beam, runner and GCP state.
    """
    info: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "beam_version": None,
        "runner": DEFAULT_RUNNER,
        "gcloud_available": has_gcloud(),
        "project_id": os.environ.get("PROJECT_ID"),
        "region": os.environ.get("REGION", "us-central1"),
        "bucket": os.environ.get("BUCKET"),
        "staging_location": os.environ.get("STAGING_LOCATION"),
        "temp_location": os.environ.get("TEMP_LOCATION"),
        "service_account": os.environ.get("SERVICE_ACCOUNT_EMAIL"),
    }

    try:
        import apache_beam

        info["beam_version"] = apache_beam.__version__
    except ImportError:
        log.warning("apache-beam is not installed — install resources/requirements.txt")

    return info


# --------------------------------------------------------------------------
# Option resolution
# --------------------------------------------------------------------------


def build_options(argv: list[str] | None = None, **overrides: Any) -> Any:
    """Build a `PipelineOptions` object from command-line flags.

    Beam parses `--flag=value` from `argv` and attaches each known flag to
    the relevant options subclass. Unknown flags are ignored with a
    warning, which is why the course code passes the raw argv rather than
    a hand-built dict — the runner flag and the streaming flag
    `--allow_unsafe_triggers` are both resolved correctly without any
    special-casing here.

    Args:
        argv: The raw argument list, usually `sys.argv[1:]`.
        **overrides: Extra options applied after parsing.

    Returns:
        A `PipelineOptions` instance.
    """
    from apache_beam.options.pipeline_options import PipelineOptions

    options = PipelineOptions(argv if argv is not None else [])
    for name, value in overrides.items():
        if value is not None:
            setattr(options, name, value)
    return options


def resolve_runner(options: Any) -> str:
    """Return the runner name an options object selects.

    Args:
        options: A `PipelineOptions` instance.

    Returns:
        The runner class name, e.g. `"BundleBasedDirectRunner"`.
    """
    runner = getattr(options, "runner", None)
    if runner is None:
        return DEFAULT_RUNNER
    # `runner` is a read-only property that resolves the string to a class.
    return getattr(runner, "__name__", str(runner))


def is_local(runner_name: str) -> bool:
    """Return True when the runner needs no cloud credentials.

    Args:
        runner_name: The runner class name.

    Returns:
        True for a local runner.
    """
    return runner_name in LOCAL_RUNNERS


# --------------------------------------------------------------------------
# Job submission
# --------------------------------------------------------------------------


def _run_gcloud(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a `gcloud` command and return the completed process.

    Args:
        args: The arguments after `gcloud`.
        check: When True, a non-zero exit raises `CalledProcessError`.

    Returns:
        The completed process.
    """
    if not has_gcloud():
        raise RuntimeError(
            "the gcloud CLI is not installed — see resources/SETUP.md for installation"
        )
    cmd = ["gcloud", *args]
    log.info("running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def submit_dataflow_job(
    *,
    job_name: str,
    gcs_path: str,
    project: str | None = None,
    region: str | None = None,
    temp_location: str | None = None,
    staging_location: str | None = None,
    service_account_email: str | None = None,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Submit a Python pipeline to Dataflow as a flex template job.

    This mirrors what `gcloud dataflow flex-template run` does, but
    returns structured data so a notebook can print the job ID without
    shelling out to `jq`.

    Args:
        job_name: The Dataflow job name.
        gcs_path: The `gs://` path of the uploaded worker script.
        project: The GCP project ID.
        region: The Dataflow region.
        temp_location: The `gs://` temp path.
        staging_location: The `gs://` staging path.
        service_account_email: The worker service account.
        extra_args: Extra flags passed straight through to `gcloud`.

    Returns:
        A dict with the job name, job ID and the command that was run.

    Raises:
        RuntimeError: If `gcloud` is not installed or the submission fails.
    """
    project = project or os.environ.get("PROJECT_ID")
    region = region or os.environ.get("REGION", "us-central1")
    temp_location = temp_location or os.environ.get("TEMP_LOCATION")
    staging_location = staging_location or os.environ.get("STAGING_LOCATION")
    service_account_email = service_account_email or os.environ.get(
        "SERVICE_ACCOUNT_EMAIL"
    )

    missing = [
        name
        for name, value in (
            ("PROJECT_ID", project),
            ("TEMP_LOCATION", temp_location),
            ("STAGING_LOCATION", staging_location),
            ("SERVICE_ACCOUNT_EMAIL", service_account_email),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "missing Dataflow configuration: "
            + ", ".join(missing)
            + " — see resources/SETUP.md"
        )

    args = [
        "dataflow",
        "flex-template",
        "run",
        f"--job-name={job_name}",
        f"--project={project}",
        f"--region={region}",
        f"--temp-location={temp_location}",
        f"--staging-location={staging_location}",
        f"--service-account={service_account_email}",
        f"--template={gcs_path}",
        "--wait=false",
    ]
    if extra_args:
        args.extend(extra_args)

    result = _run_gcloud(args, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"gcloud failed:\n{result.stderr or result.stdout}")

    job_id = _extract_job_id(result.stdout)
    return {
        "job_name": job_name,
        "job_id": job_id,
        "project": project,
        "region": region,
        "command": " ".join(["gcloud", *args]),
    }


def _extract_job_id(output: str) -> str | None:
    """Pull the Dataflow job ID out of `gcloud` output.

    Args:
        output: The combined stdout of the gcloud command.

    Returns:
        The job ID, or None if it could not be found.
    """
    for token in output.replace(",", " ").split():
        stripped = token.strip("\"'")
        if stripped.startswith("202") and "-" in stripped and len(stripped) > 20:
            return stripped
    return None


def describe_job(job_id: str, *, project: str | None = None) -> dict[str, Any]:
    """Fetch the state of a Dataflow job.

    Args:
        job_id: The Dataflow job ID.
        project: The GCP project ID.

    Returns:
        A dict with the job's current state and metadata.
    """
    project = project or os.environ.get("PROJECT_ID")
    if not project:
        raise RuntimeError("PROJECT_ID is not set")

    result = _run_gcloud(
        [
            "dataflow",
            "jobs",
            "describe",
            job_id,
            f"--project={project}",
            "--format=json",
        ]
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        log.warning("could not parse the job description as JSON")
        return {"raw": result.stdout}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Print the environment summary.

    Args:
        argv: The argument list.

    Returns:
        0 on success.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runner", help="Show the options a runner would produce")
    parser.add_argument("--json", action="store_true", help="Print JSON, not a table")
    args = parser.parse_args(argv)

    load_dotenv()
    info = describe_environment()

    if args.json:
        print(json.dumps(info, indent=2))
        return 0

    print("=" * 62)
    print("DATAFLOW COURSE ENVIRONMENT")
    print("=" * 62)
    for key, value in info.items():
        print(f"  {key:20} {value}")

    if args.runner:
        options = build_options([f"--runner={args.runner}"])
        print()
        print(f"  runner resolves to: {resolve_runner(options)}")
        print(f"  local (no creds):   {is_local(resolve_runner(options))}")

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(main())
