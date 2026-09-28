"""Tests for the test runner."""

import textwrap
from pathlib import Path

import pytest

from agent.runner import run_tests
from agent.schemas import RunTestsArgs


@pytest.fixture
def passing_repo(tmp_path: Path) -> Path:
    (tmp_path / "test_pass.py").write_text(textwrap.dedent("""
        def test_one():
            assert 1 + 1 == 2
        def test_two():
            assert "a" + "b" == "ab"
    """))
    return tmp_path


@pytest.fixture
def failing_repo(tmp_path: Path) -> Path:
    (tmp_path / "test_fail.py").write_text(textwrap.dedent("""
        def test_ok():
            assert 1 + 1 == 2
        def test_broken():
            assert 1 + 1 == 3
    """))
    return tmp_path


def test_run_passing_tests(passing_repo):
    res = run_tests(passing_repo, RunTestsArgs(target=""))
    assert res.passed
    assert res.failures == []


def test_run_failing_tests_captures_failure(failing_repo):
    res = run_tests(failing_repo, RunTestsArgs(target=""))
    assert not res.passed
    assert len(res.failures) >= 1
    assert any("test_broken" in f["test"] for f in res.failures)


def test_run_specific_test(failing_repo):
    res = run_tests(failing_repo, RunTestsArgs(target="test_fail.py::test_ok"))
    assert res.passed


def test_run_respects_timeout(tmp_path):
    (tmp_path / "test_slow.py").write_text("import time\ndef test_slow():\n    time.sleep(10)\n")
    res = run_tests(tmp_path, RunTestsArgs(target="", timeout_s=3))
    assert not res.passed
    assert res.exit_code == 124
    assert any("timed out" in f["msg"].lower() for f in res.failures)