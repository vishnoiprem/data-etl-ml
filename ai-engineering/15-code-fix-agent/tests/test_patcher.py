"""Tests for the patcher — apply_edits must validate uniqueness and atomic rollback."""

import pytest
from pathlib import Path

from agent.patcher import apply_edits, EditError
from agent.schemas import ApplyEditsArgs, FileEdit


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "foo.py").write_text(
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "def div(a, b):\n"
        "    return a / b\n"
    )
    (tmp_path / "bar.py").write_text("VALUE = 42\n")
    return tmp_path


def test_apply_single_edit(sample_repo):
    diff = apply_edits(sample_repo, ApplyEditsArgs(edits=[
        FileEdit(
            path="foo.py",
            old_text="    return a + b",
            new_text="    return a + b  # sum",
            rationale="annotate add",
        ),
    ]))
    assert "sum" in (sample_repo / "foo.py").read_text()
    assert "+ b  # sum" in diff


def test_apply_multiple_edits_atomic(sample_repo):
    apply_edits(sample_repo, ApplyEditsArgs(edits=[
        FileEdit(path="foo.py", old_text="    return a + b",
                 new_text="    return float(a) + float(b)", rationale="coerce"),
        FileEdit(path="foo.py", old_text="    return a / b",
                 new_text="    return float(a) / float(b)", rationale="coerce"),
        FileEdit(path="bar.py", old_text="VALUE = 42", new_text="VALUE = 4.2", rationale="fraction"),
    ]))
    foo = (sample_repo / "foo.py").read_text()
    assert "float(a) + float(b)" in foo
    assert "float(a) / float(b)" in foo
    assert "VALUE = 4.2" in (sample_repo / "bar.py").read_text()


def test_old_text_must_be_unique(sample_repo):
    with pytest.raises(EditError, match="ambiguous"):
        apply_edits(sample_repo, ApplyEditsArgs(edits=[
            FileEdit(path="foo.py", old_text="def",
                     new_text="function", rationale="short"),
        ]))


def test_old_text_must_exist(sample_repo):
    with pytest.raises(EditError, match="not found"):
        apply_edits(sample_repo, ApplyEditsArgs(edits=[
            FileEdit(path="foo.py", old_text="non-existent string",
                     new_text="x", rationale="bogus"),
        ]))


def test_file_must_exist(sample_repo):
    with pytest.raises(EditError, match="file not found"):
        apply_edits(sample_repo, ApplyEditsArgs(edits=[
            FileEdit(path="missing.py", old_text="x", new_text="y", rationale="n/a"),
        ]))


def test_atomic_failure_preserves_files(sample_repo):
    original_foo = (sample_repo / "foo.py").read_text()
    original_bar = (sample_repo / "bar.py").read_text()
    with pytest.raises(EditError):
        apply_edits(sample_repo, ApplyEditsArgs(edits=[
            FileEdit(path="foo.py", old_text="def add(a, b):",
                     new_text="def add(a, b, c):", rationale="ok"),
            FileEdit(path="bar.py", old_text="WRONG", new_text="x", rationale="will fail"),
        ]))
    assert (sample_repo / "foo.py").read_text() == original_foo
    assert (sample_repo / "bar.py").read_text() == original_bar


def test_dry_run_does_not_modify(sample_repo):
    original = (sample_repo / "foo.py").read_text()
    apply_edits(sample_repo, ApplyEditsArgs(edits=[
        FileEdit(path="foo.py", old_text="    return a + b",
                 new_text="    return a + b  # changed", rationale="annotate"),
    ]), dry_run=True)
    assert (sample_repo / "foo.py").read_text() == original