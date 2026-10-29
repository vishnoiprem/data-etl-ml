"""
conftest.py — pytest configuration for the course project tests.

Two settings matter here.

**The runner.** Beam 2.60+ ships a new Go-based in-process runner under the
name `DirectRunner` (the "Prism" runner), which is faster but does not yet
support every trigger and windowing combination — it panics on the
`AfterWatermark` trigger and on the `+inf` watermark evaluation that
`TestPipeline` performs at the end of a run.

The classic, pure-Python runner is `BundleBasedDirectRunner`. It supports
the full feature set, which is what a course needs: the code you read here
runs the same way on Dataflow.

**Unsafe triggers.** Beam refuses `AfterCount` triggers by default, because
a window can close while elements are still in flight. The trigger tests
deliberately exercise that behaviour, so the flag is set for the test run
only. See `test_options()` below.

Usage:
    python3 -m pytest project/tests/ -v
"""
from __future__ import annotations

import os

import pytest

#: The runner the tests use. Override with the `BEAM_TEST_RUNNER` env var.
TEST_RUNNER = os.environ.get("BEAM_TEST_RUNNER", "BundleBasedDirectRunner")


@pytest.fixture(scope="session", autouse=True)
def _beam_test_runner():
    """Point every `TestPipeline` in the suite at the classic runner.

    `TestPipeline` reads the runner from the `BEAM_RUNNER` environment
    variable when it is not given one explicitly, so setting it here
    covers every test in the suite.
    """
    previous = os.environ.get("BEAM_RUNNER")
    os.environ["BEAM_RUNNER"] = TEST_RUNNER
    yield TEST_RUNNER
    if previous is None:
        os.environ.pop("BEAM_RUNNER", None)
    else:
        os.environ["BEAM_RUNNER"] = previous


def beam_test_options(**extra: str):
    """Build PipelineOptions for a test pipeline.

    `TestPipeline` reads its runner from the `BEAM_RUNNER` environment
    variable, but the `allow_unsafe_triggers` flag lives on
    `TypeOptions` and has to be passed explicitly.

    The function is deliberately **not** named `test_options` — pytest
    would collect it as a test case and fail on its return value.

    Args:
        **extra: Extra command line flags to pass through.

    Returns:
        A PipelineOptions instance for the test pipeline.
    """
    from apache_beam.options.pipeline_options import PipelineOptions, TypeOptions

    flags = [f"--runner={TEST_RUNNER}", "--allow_unsafe_triggers"]
    flags.extend(f"--{name}={value}" for name, value in extra.items())

    options = PipelineOptions(flags)
    options.view_as(TypeOptions).allow_unsafe_triggers = True
    return options
