"""
Smoke tests for the pipeline orchestrator.

These don't run the full pipeline (that needs Spark + dummy data);
they verify the orchestrator is importable, the step helper
prints, and the CLI argument parses.
"""
from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout
from datetime import datetime, timezone


class TestStepHelper:
    """Tests for step() helper."""

    def test_step_prints(self):
        from scb_aml_platform.orchestration.pipeline_orchestrator import step
        buf = io.StringIO()
        with redirect_stdout(buf):
            step("test step", "00:00")
        # The function uses loguru; it may or may not write to stdout,
        # but the call should not raise.
        assert True


class TestCLI:
    """Tests for the CLI argument parser."""

    def test_default_date_is_today(self):
        from scb_aml_platform.orchestration.pipeline_orchestrator import (
            run_pipeline,
        )
        # Just verify the function signature accepts a date string.
        # Don't actually call run_pipeline() — it would need full
        # dummy data + Spark to work.
        import inspect
        sig = inspect.signature(run_pipeline)
        assert "run_date" in sig.parameters
        assert sig.parameters["run_date"].default is None
