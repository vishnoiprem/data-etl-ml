"""Tests for the course linter's snippet checks.

The linter is only worth running if its checks actually fire. A check
that silently passes everything is worse than no check at all: it
reports "clean" while a reader-facing defect sits in a chapter.

These tests pin the behaviour of the checks that catch real defects:
a missing ``dataclass`` import, a missing base-class import, and the
false positives that a naive implementation would produce.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parent.parent.parent / "resources"
COURSE_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_audit():
    """Load the linter module by path.

    The linter is a script rather than an installed package, so it is
    loaded from its file rather than imported by name.

    Returns:
        The loaded module.
    """
    spec = importlib.util.spec_from_file_location(
        "audit_course", RESOURCES / "audit_course.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = _load_audit()


# --------------------------------------------------------------------------
# The static decorator / base-class check
# --------------------------------------------------------------------------


def _undefined(source: str, prose: str = "") -> set[str]:
    """Run the static check over a snippet.

    Args:
        source: The snippet source.
        prose: The chapter prose the snippet sits in.

    Returns:
        The set of undefined decorator or base-class names.
    """
    tree = ast.parse(source)
    return audit._undefined_decorators_or_bases(tree, audit._prose_import_names(prose))


def test_missing_dataclass_import_is_caught():
    """The bug this check exists for must be caught."""
    source = """
from dataclasses import field

@dataclass(frozen=True)
class Option:
    name: str
"""
    assert "dataclass" in _undefined(source)


def test_present_dataclass_import_is_not_flagged():
    """A snippet that imports what it uses must pass."""
    source = """
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Option:
    name: str
"""
    assert _undefined(source) == set()


def test_missing_base_class_import_is_caught():
    """A base class is an import too, and must be checked."""
    source = """
class Probe(SpecialBase):
    pass
"""
    assert "SpecialBase" in _undefined(source)


def test_base_class_defined_in_the_same_block_passes():
    """A base class defined locally needs no import."""
    source = """
class Base:
    pass

class Probe(Base):
    pass
"""
    assert _undefined(source) == set()


def test_base_class_from_another_snippet_does_not_satisfy_the_check():
    """A name bound by an earlier block is not an import.

    The reader may save the later block on its own, so the import has
    to be present in the block that uses the name.
    """
    source = """
class Probe(ElsewhereDefined):
    pass
"""
    # The name is not imported here, so it must be reported.
    assert "ElsewhereDefined" in _undefined(source)


def test_prose_import_satisfies_the_check():
    """A name the prose says to import is legitimately imported."""
    source = """
@task
def extract():
    return {}
"""
    prose = "Airflow's decorator comes from `from airflow.decorators import task`."
    assert _undefined(source, prose) == set()


def test_builtin_decorator_is_not_flagged():
    """``@property`` is a builtin and needs no import."""
    source = """
class Thing:
    @property
    def value(self):
        return 1
"""
    assert _undefined(source) == set()


def test_called_decorator_is_checked():
    """A decorator applied as a call is still a decorator."""
    source = """
@register
class Thing:
    pass
"""
    assert "register" in _undefined(source)


# --------------------------------------------------------------------------
# The prose-import extraction
# --------------------------------------------------------------------------


def test_prose_import_names_ignores_code_fences():
    """An import inside a code block is not a prose import."""
    text = "Prose here.\n\n```python\nfrom x import y\n```\n\nMore prose.\n"
    assert "y" not in audit._prose_import_names(text)


def test_prose_import_names_finds_bare_import():
    """A bare ``import x`` in prose counts."""
    text = "You will need `import pandas` to follow along."
    assert "pandas" in audit._prose_import_names(text)


def test_prose_import_names_finds_backticked_decorator():
    """A ``@name`` mentioned in prose counts."""
    text = "Airflow's `@task` decorator marks a Python callable as a task."
    assert "task" in audit._prose_import_names(text)


# --------------------------------------------------------------------------
# The snippet executor
# --------------------------------------------------------------------------


def _run_snippet(tmp_path: Path, source: str) -> list[str]:
    """Execute one snippet through the linter and return the errors.

    Args:
        tmp_path: A directory for the temporary chapter file.
        source: The snippet source.

    Returns:
        The error messages the linter produced.
    """
    chapter = tmp_path / "chapter.md"
    chapter.write_text(f"```python\n{source}\n```\n", encoding="utf-8")
    report = audit.Report()
    audit.check_snippet_execution(chapter, report)
    return report.errors


def test_snippet_with_missing_import_is_reported(tmp_path):
    """A snippet that raises NameError must be reported."""
    errors = _run_snippet(
        tmp_path,
        """
import sys
from dataclasses import dataclass

@dataclass
class Probe:
    value: int = 1

print(Probe())
""",
    )
    assert not errors, errors


def test_snippet_that_fails_to_run_is_reported(tmp_path):
    """A snippet that raises must be reported, not swallowed."""
    errors = _run_snippet(
        tmp_path,
        """
import sys

sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events

print(ingest_events(lines=None))
""",
    )
    assert errors, "a snippet that raises must be reported"
    assert "does not run" in errors[0]


def test_earlier_import_does_not_rescue_a_later_block(tmp_path):
    """A missing import in a later block must still be caught.

    This is the exact bug the check was written for: block one
    imports ``dataclass``, block two uses it without importing it.
    Sharing one namespace across a chapter would hide it.
    """
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        "```python\n"
        "from dataclasses import dataclass, field\n"
        "\n"
        "@dataclass\n"
        "class First:\n"
        "    value: int = 1\n"
        "```\n"
        "\n"
        "```python\n"
        "@dataclass\n"
        "class Second:\n"
        "    value: int = 1\n"
        "```\n",
        encoding="utf-8",
    )
    report = audit.Report()
    audit.check_snippet_execution(chapter, report)
    assert any("dataclass" in error for error in report.errors), report.errors


# --------------------------------------------------------------------------
# The course itself
# --------------------------------------------------------------------------


def test_every_chapter_has_snippets_that_run():
    """No chapter may contain a snippet that fails to run."""
    report = audit.Report()
    for chapter in sorted((COURSE_ROOT / "chapters").glob("*.md")):
        audit.check_snippet_execution(chapter, report)
    assert not report.errors, report.errors


def test_the_linter_reports_no_errors_on_the_course():
    """The whole course must pass the linter.

    This is the single most valuable test in the file: it fails the
    moment a chapter snippet breaks.
    """
    # An explicit argv: pytest's own command line would otherwise be
    # parsed as the linter's arguments.
    assert audit.main([]) == 0
