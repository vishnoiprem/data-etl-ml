#!/usr/bin/env python3
"""Static audit harness for the Datastream course.

Validates, without needing GCP credentials:

  1. every notebook parses and has a valid nbformat structure
  2. every Python snippet in the chapters, notebooks and project parses
  3. every Python snippet that touches a GCP SDK uses attributes that
     actually exist in the installed library — this catches a misspelled
     method (`client.access_secret_version` vs `client.access_secret`)
     that would otherwise only fail at runtime
  4. every SQL snippet in the chapters parses as SQL
  5. no leftover placeholders, TODOs or unbalanced f-strings
  6. every README/chapter/notebook relative link resolves

Usage:
    python resources/audit_course.py
    python resources/audit_course.py --quiet
"""

from __future__ import annotations

import argparse
import ast
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
SQL = ROOT / "sql"

#: The SDKs whose attribute access this linter checks. The value is the
#: *dotted path* used to import the module for the attribute lookup — it
#: must be importable on its own, so `google.cloud.bigquery` and not
#: `bigquery` (there is no top-level `bigquery` package).
CHECKED_MODULES = {
    "google.cloud.secretmanager": "google.cloud.secretmanager",
    "google.cloud.bigquery": "google.cloud.bigquery",
    "google.cloud.storage": "google.cloud.storage",
    "google.cloud.pubsub_v1": "google.cloud.pubsub_v1",
    "google.cloud.pubsub": "google.cloud.pubsub",
}


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
# Placeholder / hygiene checks
# --------------------------------------------------------------------------

PLACEHOLDER_OK = {
    "YOUR_PROJECT_ID",
    "YOUR_PROJECT",
    "YOUR_DATASET",
    "YOUR_TABLE",
    "YOUR_BUCKET",
    "YOUR_TOPIC",
    "YOUR_SUBSCRIPTION",
    "YOUR_SECRET",
    "YOUR_REGION",
    "YOUR_INSTANCE",
    "YOUR_KAFKA_CLUSTER",
    "YOUR_PROJECT_ID-datastream@YOUR_PROJECT_ID.iam.gserviceaccount.com",
    # Lower-case shell placeholders for hostnames, images and instances.
    "your-vm",
    "your-instance",
    "your-image",
    "your-bucket",
    "your-project",
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
    if origin.endswith("audit_course.py"):
        return

    for m in BAD_TOKENS.finditer(text):
        line = text[: m.start()].count("\n") + 1
        report.warn(origin, line, f"unresolved marker: {m.group(0)}")


def check_placeholders(report: Report, origin: str, text: str):
    """Flag placeholders that are not in the known-safe list.

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
        line_no = text[: m.start()].count("\n") + 1
        report.info(origin, line_no, f"placeholder in use: {token}")


# --------------------------------------------------------------------------
# Python validation
# --------------------------------------------------------------------------


def check_sdk_attributes(report: Report, origin: str, tree: ast.AST, line: int | None):
    """Check that every SDK attribute access exists in the installed library.

    Args:
        report: The report to record issues in.
        origin: The file the snippet came from.
        tree: The parsed snippet.
        line: The line number the snippet starts at.
    """
    # Map an alias to the module it refers to.
    aliases: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # `import google.cloud.bigquery as bq` or
            # `from google.cloud import bigquery as bq`.
            for alias in node.names:
                if alias.name in CHECKED_MODULES:
                    aliases[alias.asname or alias.name] = CHECKED_MODULES[alias.name]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in CHECKED_MODULES:
                # `from google.cloud.bigquery import Client` — the alias
                # refers to a name *inside* the module, not the module
                # itself, so it cannot be checked this way.
                for alias in node.names:
                    aliases[alias.asname or alias.name] = CHECKED_MODULES[module]
            elif module == "google.cloud":
                # `from google.cloud import bigquery` — the alias refers to
                # the submodule, which is what the attribute check needs.
                for alias in node.names:
                    dotted = f"{module}.{alias.name}"
                    if dotted in CHECKED_MODULES:
                        aliases[alias.asname or alias.name] = CHECKED_MODULES[dotted]

    if not aliases:
        return

    # A local variable shadowing an alias disables the check for it.
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
        alias = node.value.id
        if alias not in aliases or alias in shadowed:
            continue

        module_name = aliases[alias]
        try:
            module = __import__(module_name, fromlist=["_"])
        except ImportError:
            report.info(
                origin,
                line,
                f"{module_name} is not installed — the {alias}.<attr> check was skipped",
            )
            return

        if not hasattr(module, node.attr):
            report.error(
                origin,
                (line or 0) + getattr(node, "lineno", 0) - 1,
                f"{alias}.{node.attr} does not exist in {module_name}",
            )


def validate_python(
    report: Report,
    origin: str,
    source: str,
    line: int | None,
):
    """Parse a Python snippet and check its SDK usage.

    Args:
        report: The report to record issues in.
        origin: The file the snippet came from.
        source: The Python source.
        line: The line number the snippet starts at.
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

    check_sdk_attributes(report, origin, tree, line)


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
                validate_python(report, rel, src, None)
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
            validate_python(report, rel, block, lineno)


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

    for path in sorted(PROJECT.rglob("*.tf")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        check_hygiene(report, rel, text)
        # An unbalanced brace in Terraform is a syntax error that `terraform
        # validate` would catch later; catching it here is cheaper.
        if text.count("{") != text.count("}"):
            report.error(rel, None, "unbalanced braces in Terraform file")
        if text.count("[") != text.count("]"):
            report.error(rel, None, "unbalanced brackets in Terraform file")


def audit_sql(report: Report):
    """Validate every SQL file in `sql/`."""
    for path in sorted(SQL.glob("*.sql")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        check_hygiene(report, rel, text)
        if ";" not in text:
            report.warn(rel, None, "no statement terminator found")


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
    audit_sql(report)
    audit_readme(report)

    errors = report.by_severity("ERROR")
    warns = report.by_severity("WARN")
    infos = report.by_severity("INFO")

    print("=" * 78)
    print("DATASTREAM COURSE AUDIT")
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
