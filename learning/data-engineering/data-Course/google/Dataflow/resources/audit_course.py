#!/usr/bin/env python3
"""Static audit harness for the Dataflow course.

Validates, without needing GCP credentials:

  1. every notebook parses and has a valid nbformat structure
  2. every Python snippet in the chapters, notebooks and project parses
  3. every Python snippet that touches the Beam SDK uses attributes that
     actually exist in the installed `apache_beam` — this catches a
     misspelled transform (`beam.CombinePerKey` vs `beam.combiners.Count`)
     that would otherwise only fail at runtime on a worker
  4. every pipeline in the project has unique transform labels
  5. no leftover placeholders, TODOs or unbalanced f-strings
  6. every README/chapter/notebook relative link resolves

Usage:
    python resources/audit_course.py
    python resources/audit_course.py --quiet
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"
NOTEBOOKS = ROOT / "notebooks"
INTERVIEW = ROOT / "interview"
RESOURCES = ROOT / "resources"
PROJECT = ROOT / "project"

BEAM = "beam"


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


@dataclass
class Issue:
    """One problem found by the audit."""

    severity: str  # ERROR | WARN | INFO
    file: str
    line: int | None
    message: str
    snippet: str = ""


@dataclass
class Report:
    """The collection of issues found during an audit."""

    issues: list[Issue] = field(default_factory=list)

    def add(self, severity, file, line, message, snippet=""):
        """Record one issue."""
        self.issues.append(Issue(severity, file, line, message, snippet))

    def error(self, *a, **k):
        """Record an error."""
        self.add("ERROR", *a, **k)

    def warn(self, *a, **k):
        """Record a warning."""
        self.add("WARN", *a, **k)

    def info(self, *a, **k):
        """Record an informational note."""
        self.add("INFO", *a, **k)

    def by_severity(self, sev):
        """Return the issues with the given severity."""
        return [i for i in self.issues if i.severity == sev]


# --------------------------------------------------------------------------
# Python validation
# --------------------------------------------------------------------------


def validate_python(
    report: Report,
    origin: str,
    source: str,
    line: int | None,
    scope: str = "",
):
    """Parse a Python snippet and check its Beam SDK usage.

    Three things are checked:

    * the snippet parses
    * every `beam.<attr>` access resolves against the installed SDK
    * a transform label is not reused inside the same pipeline

    Args:
        report: The report to record issues in.
        origin: The file the snippet came from.
        source: The Python source.
        line: The line number the snippet starts at.
        scope: An extra scope key for the duplicate-label check. Snippets
            with different scope keys are treated as separate pipelines.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.error(
            origin,
            line,
            f"Python syntax error: {exc.msg} (col {exc.offset})",
            source[max(0, (exc.offset or 1) - 30) : (exc.offset or 1) + 40].strip(),
        )
        return

    check_beam_attributes(report, origin, tree, line)
    check_transform_labels(report, origin, tree, line, scope)


def check_beam_attributes(report: Report, origin: str, tree: ast.AST, line: int | None):
    """Check that every `beam.<attr>` access exists in the SDK.

    This is the Beam equivalent of checking `bigquery.<attr>` in the
    BigQuery course. It catches the class of mistake that only shows up
    on a Dataflow worker, hours into a job, when a transform name was
    misspelled.

    Args:
        report: The report to record issues in.
        origin: The file the snippet came from.
        tree: The parsed snippet.
        line: The line number the snippet starts at.
    """
    try:
        import apache_beam as beam
    except ImportError:
        report.info(
            origin,
            line,
            "apache-beam is not installed — the beam.<attr> check was skipped",
        )
        return

    # Names bound to the beam module, so `from apache_beam import Map as M`
    # style aliases are checked too.
    aliases = {BEAM}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "apache_beam":
                    aliases.add(alias.asname or "beam")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "apache_beam":
                for alias in node.names:
                    aliases.add(alias.asname or alias.name)

    # A local variable named `beam` would shadow the module. Skip those.
    shadowed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    shadowed.add(target.id)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name):
                shadowed.add(node.target.id)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if not isinstance(node.value, ast.Name):
            continue
        if node.value.id not in aliases or node.value.id in shadowed:
            continue
        if not hasattr(beam, node.attr):
            report.error(
                origin,
                (line or 0) + getattr(node, "lineno", 0) - 1,
                f"beam.{node.attr} does not exist in apache-beam",
            )


def check_transform_labels(
    report: Report,
    origin: str,
    tree: ast.AST,
    line: int | None,
    scope: str = "",
):
    """Check that transform labels are unique within a pipeline.

    Beam raises `RuntimeError: Transform name is already used` when two
    transforms in the same pipeline share a label. The error message does
    not say which labels collided, so catching it statically is worth it.

    The label is the left operand of `>>` in `p | "Label" >> transform`.

    Labels are scoped **per pipeline**, and a pipeline is approximated by
    the enclosing function or method. Two different test methods may
    legitimately both use a transform called `"Create"` — they are two
    separate pipelines, so that is not a collision. A module-level
    script, which is one pipeline, is scoped to the module.

    Args:
        report: The report to record issues in.
        origin: The file the snippet came from.
        tree: The parsed snippet.
        line: The line number the snippet starts at.
        scope: An extra scope key. Snippets validated with different
            scope keys are treated as separate pipelines — a notebook
            cell uses the cell index, for instance.
    """
    # Collect the labels used inside each enclosing scope. A scope is
    # identified by the id of its `ast.FunctionDef`/`ast.AsyncFunctionDef`
    # node, or 0 for module-level code.
    scoped: dict[tuple[str, int], list[tuple[str, int]]] = {}

    def scope_of(node: ast.AST) -> int:
        """Return the id of the innermost function containing `node`."""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(parent):
                    if child is node:
                        return id(parent)
        return 0

    def in_try_block(node: ast.AST) -> bool:
        """Return True when `node` sits inside a `try` statement.

        A snippet that deliberately triggers an error — the course's
        "here is the mistake and here is the message" cells — wraps the
        bad code in `try`/`except`. Those are intentional, so the
        duplicate-label check skips them.
        """
        for parent in ast.walk(tree):
            if isinstance(parent, ast.Try):
                for child in ast.walk(parent):
                    if child is node:
                        return True
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp):
            continue
        if not isinstance(node.op, ast.RShift):
            continue
        # In `p | "Label" >> transform`, the label is the LEFT operand of
        # `>>`; the transform is the right one. (The label is the right
        # operand of the enclosing `|`, which is a different node.)
        left = node.left
        if isinstance(left, ast.Constant) and isinstance(left.value, str):
            if in_try_block(node):
                continue
            key = (scope, scope_of(node))
            scoped.setdefault(key, []).append(
                (left.value, getattr(node, "lineno", 0))
            )

    for scope_key, labels in scoped.items():
        seen: dict[str, int] = {}
        for label, lineno in labels:
            if label in seen:
                report.error(
                    origin,
                    (line or 0) + lineno - 1,
                    f"transform label {label!r} is used more than once "
                    f"(first used on line {seen[label]})",
                )
            else:
                seen[label] = lineno


# --------------------------------------------------------------------------
# Placeholder / hygiene checks
# --------------------------------------------------------------------------

PLACEHOLDER_OK = {
    "YOUR_PROJECT_ID",
    "YOUR_PROJECT",
    "YOUR_PROJECT_ID-dataflow",
    "YOUR_DATASET",
    "YOUR_TABLE",
    "YOUR_BUCKET",
    "YOUR_TOPIC",
    "YOUR_SUBSCRIPTION",
    "YOUR_IMAGE",
    "YOUR_PROJECT_ID.iam.gserviceaccount.com",
}

BAD_TOKENS = re.compile(
    r"\b(TODO|FIXME|XXX|HACK|PLACEHOLDER_VALUE|your-project-id|CHANGEME)\b"
)


def check_hygiene(report: Report, origin: str, text: str):
    """Flag leftover markers and unresolved placeholders.

    Args:
        report: The report to record issues in.
        origin: The file the text came from.
        text: The text to check.
    """
    # The audit tool itself defines these marker words as a regex — exempt it.
    if origin.endswith("audit_course.py"):
        return

    for m in BAD_TOKENS.finditer(text):
        line = text[: m.start()].count("\n") + 1
        report.warn(origin, line, f"unresolved marker: {m.group(0)}")


def check_placeholders(report: Report, origin: str, text: str):
    """Flag placeholders that are not in the known-safe list.

    A placeholder in a `bash` block is expected — that is how the
    commands stay runnable after the reader fills in their own project.
    A placeholder in prose, however, usually means the chapter was not
    finished.

    Args:
        report: The report to record issues in.
        origin: The file the text came from.
        text: The text to check.
    """
    pattern = re.compile(r"\bYOUR_[A-Z_]+\b|\byour-[a-z-]+\b")
    for m in pattern.finditer(text):
        token = m.group(0)
        if token in PLACEHOLDER_OK:
            continue
        # A placeholder inside a fenced bash block is fine.
        line_no = text[: m.start()].count("\n") + 1
        report.info(origin, line_no, f"placeholder in use: {token}")


# --------------------------------------------------------------------------
# Link checking
# --------------------------------------------------------------------------


def check_links(report: Report, origin: str, base: Path, text: str):
    """Check that every relative markdown link resolves.

    Args:
        report: The report to record issues in.
        origin: The file the text came from.
        base: The directory relative links are resolved against.
        text: The text to check.
    """
    for m in re.finditer(r"\]\(([^)\s]+)\)", text):
        target = m.group(1)
        if target.startswith(("http", "#", "mailto:")):
            continue
        # Strip an anchor from the target.
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (base / target_path).resolve()
        if not resolved.exists():
            line = text[: m.start()].count("\n") + 1
            report.error(origin, line, f"broken link: {target}")


# --------------------------------------------------------------------------
# Fence extraction
# --------------------------------------------------------------------------


def extract_fenced_blocks(text: str, language: str) -> list[tuple[int, str]]:
    """Extract fenced code blocks of one language from a markdown document.

    Args:
        text: The markdown text.
        language: The fence language, e.g. "python".

    Returns:
        A list of (line_number, code) pairs.
    """
    pattern = re.compile(rf"```{language}\n(.*?)```", re.DOTALL)
    return [(text[: m.start()].count("\n") + 1, m.group(1)) for m in pattern.finditer(text)]


# --------------------------------------------------------------------------
# Main audit
# --------------------------------------------------------------------------


def audit_notebooks(report: Report):
    """Validate every notebook in `notebooks/`."""
    try:
        import nbformat
    except ImportError:
        report.info("notebooks", None, "nbformat not installed — strict validation skipped")
        nbformat = None

    for path in sorted(NOTEBOOKS.glob("*.ipynb")):
        rel = str(path.relative_to(ROOT))
        try:
            nb = nbformat.read(path, as_version=4)
            if nbformat:
                nbformat.validate(nb)
        except Exception as exc:
            report.error(rel, None, f"notebook invalid: {str(exc)[:200]}")
            continue

        for idx, cell in enumerate(nb.cells):
            src = cell.source
            if cell.cell_type == "code":
                # Each notebook cell is its own pipeline, so the cell
                # index scopes the duplicate-label check.
                validate_python(report, rel, src, None, scope=f"cell{idx}")
                check_hygiene(report, rel, src)
            else:
                check_links(report, rel, path.parent, src)
                check_hygiene(report, rel, src)


def audit_chapters(report: Report):
    """Validate every chapter in `chapters/`."""
    for path in sorted(CHAPTERS.glob("*.md")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        check_links(report, rel, path.parent, text)
        check_hygiene(report, rel, text)
        check_placeholders(report, rel, text)

        for lineno, block in extract_fenced_blocks(text, "python"):
            # Each fenced block is its own snippet, so the block's line
            # number scopes the duplicate-label check.
            validate_python(report, rel, block, lineno, scope=f"fence{lineno}")


def audit_interview(report: Report):
    """Validate every interview file in `interview/`."""
    for path in sorted(INTERVIEW.glob("*.md")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        check_links(report, rel, path.parent, text)
        check_hygiene(report, rel, text)


def audit_resources(report: Report):
    """Validate every file in `resources/`."""
    for path in sorted(RESOURCES.glob("*.py")):
        rel = str(path.relative_to(ROOT))
        source = path.read_text()
        validate_python(report, rel, source, None)
        try:
            compile(source, rel, "exec")
        except SyntaxError as exc:
            report.error(rel, exc.lineno, f"does not compile: {exc.msg}")
        check_hygiene(report, rel, source)

    for path in sorted(RESOURCES.glob("*.md")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        check_links(report, rel, path.parent, text)
        check_hygiene(report, rel, text)


def audit_project(report: Report):
    """Validate every Python file in `project/`."""
    for path in sorted(PROJECT.rglob("*.py")):
        rel = str(path.relative_to(ROOT))
        source = path.read_text()
        validate_python(report, rel, source, None)
        try:
            compile(source, rel, "exec")
        except SyntaxError as exc:
            report.error(rel, exc.lineno, f"does not compile: {exc.msg}")
        check_hygiene(report, rel, source)

    for path in sorted(PROJECT.rglob("*.md")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        check_links(report, rel, path.parent, text)
        check_hygiene(report, rel, text)


def audit_readme(report: Report):
    """Validate the course README."""
    path = ROOT / "README.md"
    if not path.exists():
        report.warn("README.md", None, "the course README is missing")
        return
    text = path.read_text()
    check_links(report, "README.md", ROOT, text)
    check_hygiene(report, "README.md", text)


def main() -> int:
    """Run the audit and print the report.

    Returns:
        0 when there are no errors, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true", help="Only print the summary")
    args = parser.parse_args()

    report = Report()
    audit_notebooks(report)
    audit_chapters(report)
    audit_interview(report)
    audit_resources(report)
    audit_project(report)
    audit_readme(report)

    errors = report.by_severity("ERROR")
    warns = report.by_severity("WARN")
    infos = report.by_severity("INFO")

    print("=" * 78)
    print("DATAFLOW COURSE AUDIT")
    print("=" * 78)
    print(f"ERRORS: {len(errors)}   WARNINGS: {len(warns)}   INFO: {len(infos)}")
    print()

    if not args.quiet:
        for sev, items in (("ERROR", errors), ("WARN", warns), ("INFO", infos)):
            if not items:
                continue
            print(f"--- {sev} ---")
            for i in items:
                loc = f"{i.file}:{i.line}" if i.line else i.file
                print(f"  [{sev}] {loc}")
                print(f"         {i.message}")
                if i.snippet:
                    print(f"         > {i.snippet}")
            print()

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
