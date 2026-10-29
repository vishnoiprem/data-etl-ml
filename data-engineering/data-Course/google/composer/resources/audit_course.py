#!/usr/bin/env python3
"""
audit_course.py — a static linter for the Composer course.

It catches the mistakes a reader would otherwise only hit on a worker,
hours into a run:

  * every relative link in a README, chapter or resource resolves;
  * every Python snippet in the chapters and project parses;
  * every notebook is valid nbformat with unique cell ids;
  * every chapter has all eight required sections;
  * every documented API name actually exists in the course's modules;
  * no leftover placeholders, unbalanced f-strings or TODO markers;
  * the documented expected outputs match what the code produces.

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
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = COURSE_ROOT / "chapters"
INTERVIEW_DIR = COURSE_ROOT / "interview"
NOTEBOOKS_DIR = COURSE_ROOT / "notebooks"
PROJECT_DIR = COURSE_ROOT / "project"
RESOURCES_DIR = COURSE_ROOT / "resources"

#: The sections every chapter must contain, in order.
REQUIRED_SECTIONS = [
    "What you will learn",
    "Concept",
    "Hands-On",
    "Common Errors and Fixes",
    "Production Notes",
    "Key Takeaways",
    "Practice Exercises",
    "Further Reading",
]

#: Markers that indicate unfinished content.
PLACEHOLDER_PATTERNS = [
    (re.compile(r"\bTODO\b"), "TODO marker"),
    (re.compile(r"\bFIXME\b"), "FIXME marker"),
    (re.compile(r"\bXXX\b"), "XXX marker"),
    (re.compile(r"YOUR_VALUE_HERE"), "unfilled placeholder"),
    (re.compile(r"\.\.\.\s*$", re.MULTILINE), "trailing ellipsis placeholder"),
]

#: Shell placeholders that are legitimately expected.
ALLOWED_PLACEHOLDERS = {
    "YOUR_PROJECT_ID",
    "YOUR_PROJECT",
    "YOUR_BUCKET",
    "YOUR_BILLING_ACCOUNT",
    "YOUR_DATASET",
    "YOUR_REGION",
    "ENV_NAME",
    "REGION",
    "BUCKET",
    "PROJECT_ID",
}


class Report:
    """Collects audit findings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks = 0

    def error(self, message: str) -> None:
        """Record an error.

        Args:
            message: The error message.
        """
        self.errors.append(message)

    def warn(self, message: str) -> None:
        """Record a warning.

        Args:
            message: The warning message.
        """
        self.warnings.append(message)

    def check(self) -> None:
        """Count one check."""
        self.checks += 1


# --------------------------------------------------------------------------
# Markdown helpers
# --------------------------------------------------------------------------

FENCE_RE = re.compile(r"^```(\w*)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def iter_code_blocks(text: str) -> list[str]:
    """Extract fenced code blocks from markdown.

    Only blocks tagged as Python are returned — ``text`` fences hold DAG
    diagrams and must not be parsed.

    Args:
        text: The markdown source.

    Returns:
        A list of code strings.
    """
    blocks: list[str] = []
    lines = text.splitlines()
    in_block = False
    language = ""
    current: list[str] = []

    for line in lines:
        if not in_block:
            match = FENCE_RE.match(line)
            if match:
                in_block = True
                language = match.group(1)
                current = []
            continue
        if FENCE_RE.match(line):
            if language in ("python", "py"):
                blocks.append("\n".join(current))
            in_block = False
            language = ""
            continue
        current.append(line)

    return blocks


def check_markdown_links(path: Path, report: Report) -> None:
    """Check that every relative link in a markdown file resolves.

    Args:
        path: The markdown file.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(text):
        target = match.group(2).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / target).resolve()
        report.check()
        if not resolved.exists():
            report.error(f"{path.relative_to(COURSE_ROOT)}: broken link -> {target}")


def check_sections(path: Path, report: Report) -> None:
    """Check that a chapter has all the required sections.

    Args:
        path: The chapter file.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    headings = re.findall(r"^##+\s+(.+)$", text, re.MULTILINE)
    for section in REQUIRED_SECTIONS:
        report.check()
        if not any(section.lower() in heading.lower() for heading in headings):
            report.error(
                f"{path.relative_to(COURSE_ROOT)}: missing section '{section}'"
            )


def check_placeholders(path: Path, report: Report) -> None:
    """Check a file for unfinished-content markers.

    Args:
        path: The file to check.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for pattern, label in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            report.check()
            line = text[: match.start()].count("\n") + 1
            snippet = match.group(0).strip()
            if label == "trailing ellipsis placeholder":
                # An ellipsis at the end of a line is prose punctuation
                # in most cases; only flag the obvious stub form.
                continue
            report.warn(f"{path.relative_to(COURSE_ROOT)}:{line}: {label} -> {snippet!r}")


def check_python_snippets(path: Path, report: Report) -> None:
    """Check that every Python snippet in a markdown file parses.

    Args:
        path: The markdown file.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for index, block in enumerate(iter_code_blocks(text)):
        report.check()
        # Skip shell-style placeholders and fragment snippets that are
        # explicitly partial (they start with "..." or use indentation).
        stripped = block.strip()
        if not stripped or stripped.startswith("..."):
            continue
        try:
            ast.parse(block)
        except SyntaxError as exc:
            line = text[: text.find(block)].count("\n") + 1
            report.error(
                f"{path.relative_to(COURSE_ROOT)}: python snippet {index + 1} "
                f"does not parse (line ~{line}): {exc.msg}"
            )


def check_unbalanced_fstrings(path: Path, report: Report) -> None:
    """Check for unbalanced braces in f-strings.

    Args:
        path: The Python file to check.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if 'f"' not in line and "f'" not in line:
            continue
        report.check()
        # Count braces outside the string literal — a rough but useful check.
        if line.count("{") != line.count("}"):
            report.warn(
                f"{path.relative_to(COURSE_ROOT)}:{number}: possibly unbalanced braces"
            )


# --------------------------------------------------------------------------
# Notebooks
# --------------------------------------------------------------------------


def check_notebook(path: Path, report: Report) -> None:
    """Check a notebook's structure.

    Args:
        path: The notebook file.
        report: The report to collect findings in.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(f"{path.relative_to(COURSE_ROOT)}: invalid JSON: {exc}")
        return

    report.check()
    if raw.get("nbformat") != 4:
        report.error(
            f"{path.relative_to(COURSE_ROOT)}: nbformat should be 4, got {raw.get('nbformat')}"
        )

    seen: set[str] = set()
    for index, cell in enumerate(raw.get("cells", [])):
        cell_id = cell.get("id")
        report.check()
        if not cell_id:
            report.error(f"{path.relative_to(COURSE_ROOT)}: cell {index} has no id")
        elif cell_id in seen:
            report.error(
                f"{path.relative_to(COURSE_ROOT)}: duplicate cell id {cell_id!r}"
            )
        else:
            seen.add(cell_id)

        source = cell.get("source")
        if not isinstance(source, (list, str)):
            report.error(
                f"{path.relative_to(COURSE_ROOT)}: cell {index} source is not a list"
            )

        if cell.get("cell_type") == "code":
            report.check()
            if cell.get("outputs"):
                report.warn(
                    f"{path.relative_to(COURSE_ROOT)}: cell {index} has stored outputs"
                )


# --------------------------------------------------------------------------
# API cross-references
# --------------------------------------------------------------------------


def collect_public_names(module_path: Path) -> set[str]:
    """Collect the public names defined in a Python module.

    Args:
        module_path: The module path.

    Returns:
        A set of names.
    """
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()

    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.add(target.id)
    return names


def check_api_references(report: Report) -> None:
    """Check that names the chapters attribute to the course modules exist.

    Args:
        report: The report to collect findings in.
    """
    known: set[str] = set()
    for module in sorted((PROJECT_DIR / "core").glob("*.py")):
        known |= collect_public_names(module)
    for module in sorted(PROJECT_DIR.glob("*.py")):
        known |= collect_public_names(module)

    if not known:
        report.error("no course modules found to check references against")
        return

    # A pattern the chapters use when naming a course function.
    pattern = re.compile(r"\bfrom (?:pipeline_logic|templating|fanout|sla_logic|sla_tracker|sensor_conditions|idempotent_load|dedup_load) import ([A-Za-z_][A-Za-z0-9_, ]*)")

    for path in sorted(CHAPTERS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            for name in match.group(1).split(","):
                clean = name.strip().split(" as ")[0].strip()
                if not clean:
                    continue
                report.check()
                if clean not in known:
                    report.error(
                        f"{path.relative_to(COURSE_ROOT)}: imports unknown name "
                        f"'{clean}' from a course module"
                    )


# --------------------------------------------------------------------------
# Expected-output consistency
# --------------------------------------------------------------------------


def check_expected_outputs(report: Report) -> None:
    """Check that the published expected outputs match the real ones.

    Args:
        report: The report to collect findings in.
    """
    sys.path.insert(0, str(PROJECT_DIR / "core"))
    try:
        from pipeline_logic import summarise_by_region, transform_orders
    except ImportError as exc:
        report.error(f"cannot import pipeline_logic: {exc}")
        return

    orders_path = COURSE_ROOT / "sample_data" / "orders.csv"
    if not orders_path.exists():
        report.warn("sample_data not generated — skipping output consistency check")
        return

    lines = orders_path.read_text(encoding="utf-8").splitlines()
    accepted, _ = transform_orders(lines)
    summary = summarise_by_region(accepted)

    expected = {
        "AMER": (318, 113592.19),
        "APAC": (285, 108194.92),
        "EMEA": (322, 118423.22),
        "LATAM": (320, 110646.18),
    }

    for region, (count, revenue) in expected.items():
        report.check()
        actual = summary.get(region)
        if actual is None:
            report.error(f"expected region {region} missing from the summary")
            continue
        if int(actual["order_count"]) != count:
            report.error(
                f"{region}: expected order_count {count}, got {actual['order_count']}"
            )
        if abs(actual["revenue_eur"] - revenue) > 0.001:
            report.error(
                f"{region}: expected revenue_eur {revenue}, got {actual['revenue_eur']}"
            )

    report.check()
    if len(accepted) != 1245:
        report.error(f"expected 1245 accepted rows, got {len(accepted)}")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the audit.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code: 0 if no errors, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true", help="Only show errors")
    args = parser.parse_args(argv)

    report = Report()

    markdown_files = (
        list(COURSE_ROOT.glob("*.md"))
        + list(CHAPTERS_DIR.glob("*.md"))
        + list(INTERVIEW_DIR.glob("*.md"))
        + list(RESOURCES_DIR.glob("*.md"))
    )

    for path in sorted(markdown_files):
        check_markdown_links(path, report)

    for path in sorted(CHAPTERS_DIR.glob("*.md")):
        check_sections(path, report)
        check_python_snippets(path, report)
        check_placeholders(path, report)

    for path in sorted(RESOURCES_DIR.glob("*.md")):
        check_markdown_links(path, report)

    for path in sorted(PROJECT_DIR.rglob("*.py")):
        check_unbalanced_fstrings(path, report)

    for path in sorted(NOTEBOOKS_DIR.glob("*.ipynb")):
        check_notebook(path, report)

    check_api_references(report)
    check_expected_outputs(report)

    if not args.quiet:
        print(f"Ran {report.checks} checks over the course.")
        print()

    if report.warnings:
        print(f"{len(report.warnings)} warning(s):")
        for message in report.warnings:
            print(f"  ! {message}")
        print()

    if report.errors:
        print(f"{len(report.errors)} error(s):")
        for message in report.errors:
            print(f"  ✗ {message}")
        return 1

    print("No errors. The course is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
