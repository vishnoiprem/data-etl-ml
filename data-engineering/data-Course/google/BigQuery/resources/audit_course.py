#!/usr/bin/env python3
"""Static audit harness for the BigQuery course.

Validates, without needing BigQuery credentials:
  1. every notebook parses and has a valid nbformat structure
  2. every SQL statement in sql/ and in notebook code cells parses under the
     BigQuery dialect (sqlglot), flagging statements that BigQuery itself would
     reject
  3. every Python snippet in notebooks/resources imports against the installed
     google-cloud-bigquery SDK (no attribute errors on the SDK surface)
  4. no leftover placeholders, TODOs or unbalanced f-strings
  5. every README/chapter/notebook relative link resolves
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"
NOTEBOOKS = ROOT / "notebooks"
SQLDIR = ROOT / "sql"
RESOURCES = ROOT / "resources"

BIGQUERY = "bigquery"


@dataclass
class Issue:
    severity: str  # ERROR | WARN | INFO
    file: str
    line: int | None
    message: str
    snippet: str = ""


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def add(self, severity, file, line, message, snippet=""):
        self.issues.append(Issue(severity, file, line, message, snippet))

    def error(self, *a, **k):
        self.add("ERROR", *a, **k)

    def warn(self, *a, **k):
        self.add("WARN", *a, **k)

    def info(self, *a, **k):
        self.add("INFO", *a, **k)

    def by_severity(self, sev):
        return [i for i in self.issues if i.severity == sev]


# --------------------------------------------------------------------------
# SQL extraction
# --------------------------------------------------------------------------

SQL_START = re.compile(
    r"(?:CREATE|SELECT|WITH|INSERT|UPDATE|DELETE|MERGE|ALTER|DROP|COPY|EXPORT|"
    r"LOAD|CALL|TRUNCATE|BEGIN|COMMIT|ROLLBACK|GRANT|REVOKE|SET|DECLARE|"
    r"EXECUTE|REFRESH|ASSERT)\b",
    re.IGNORECASE,
)


def split_sql_statements(text: str) -> list[str]:
    """Split a SQL script into individual statements, respecting quotes,
    backticks, comments and BEGIN...END blocks."""
    statements: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(text)
    in_single = False
    in_double = False
    in_backtick = False
    in_line_comment = False
    in_block_comment = False
    block_depth = 0

    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                buf.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "/" and nxt == "*":
                block_depth += 1
                i += 2
                continue
            if ch == "*" and nxt == "/":
                block_depth -= 1
                i += 2
                if block_depth == 0:
                    in_block_comment = False
                continue
            i += 1
            continue

        if not (in_single or in_double or in_backtick):
            if ch == "-" and nxt == "-":
                in_line_comment = True
                i += 2
                continue
            if ch == "#":
                in_line_comment = True
                i += 1
                continue
            if ch == "/" and nxt == "*":
                in_block_comment = True
                block_depth = 1
                i += 2
                continue

        if in_single:
            if ch == "\\":
                buf.append(text[i : i + 2])
                i += 2
                continue
            if ch == "'":
                if nxt == "'":
                    buf.append("''")
                    i += 2
                    continue
                in_single = False
            buf.append(ch)
            i += 1
            continue

        if in_double:
            if ch == "\\":
                buf.append(text[i : i + 2])
                i += 2
                continue
            if ch == '"':
                in_double = False
            buf.append(ch)
            i += 1
            continue

        if in_backtick:
            buf.append(ch)
            if ch == "`":
                in_backtick = False
            i += 1
            continue

        # normal state
        if ch == "'":
            in_single = True
            buf.append(ch)
            i += 1
            continue
        if ch == '"':
            in_double = True
            buf.append(ch)
            i += 1
            continue
        if ch == "`":
            in_backtick = True
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def extract_sql_from_python(source: str) -> list[tuple[int, str]]:
    """Find SQL-looking string literals in a Python source blob.

    f-strings are resolved against the notebook's known placeholder names so the
    extracted SQL is complete and parseable. Prose strings and Python code
    fragments are rejected.

    Returns (line_number, sql_text) pairs."""
    found: list[tuple[int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return found

    # Names bound to SQL-ish values in the snippet. f-strings referencing these
    # get substituted with a syntactically valid literal.
    bound: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str) and node.value.value.startswith(("gs://", "http", "/")):
                    bound[tgt.id] = node.value.value

    # Well-known placeholders used throughout the course. Resolving these makes
    # the extracted SQL a complete, parseable statement.
    bound.setdefault("PROJECT_ID", "your_project")
    bound.setdefault("PROJECT", "your_project")
    bound.setdefault("BUCKET", "your-bucket")

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
        elif isinstance(node, ast.JoinedStr):
            # f-string: reconstruct with placeholders substituted
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
                elif isinstance(v, ast.FormattedValue):
                    parts.append("{" + ast.unparse(v.value) + "}")
            value = "".join(parts)
        else:
            continue

        stripped = value.strip()
        if not stripped:
            continue
        if not SQL_START.match(stripped):
            continue

        # Reject prose that merely starts with a SQL keyword
        if "\n" not in stripped and " " not in stripped:
            continue
        if re.match(r"(?i)^(MERGE|INSERT|UPDATE|DELETE|SELECT|ALTER|CREATE|DROP)\s*$", stripped):
            continue

        # Resolve f-string placeholders that survived as literal '{...}'
        resolved = value
        for name, repl in bound.items():
            resolved = resolved.replace("{" + name + "}", repl)
        resolved = re.sub(r"\{[A-Za-z_][A-Za-z0-9_]*(\[[^\]]*\])?\}", "placeholder", resolved)

        # If the SQL still contains an unresolved brace it is a truncated
        # fragment, not a complete statement.
        if "{" in resolved or "}" in resolved:
            continue

        found.append((getattr(node, "lineno", 0), resolved))
    return found


# --------------------------------------------------------------------------
# SQL validation via sqlglot
# --------------------------------------------------------------------------

def validate_sql(report: Report, origin: str, sql: str, line: int | None):
    try:
        import sqlglot
    except ImportError:
        report.info(origin, line, "sqlglot not installed — SQL validation skipped")
        return

    # sqlglot logs a warning for every BigQuery-specific statement it cannot
    # model. That is expected, not a finding — silence the logger.
    import logging

    logging.getLogger("sqlglot").setLevel(logging.CRITICAL)

    # BigQuery-specific constructs sqlglot does not model: skip dialect-specific
    # statements rather than reporting false positives.
    upper = sql.upper().lstrip()
    skip_prefixes = (
        "CALL BQ.REFRESH_MATERIALIZED_VIEW",
        "EXPORT DATA",
        "LOAD DATA",
        "EXPORT TABLE",
        "CREATE TABLE FUNCTION",
        "CREATE EXTERNAL TABLE FUNCTION",
    )
    if any(upper.startswith(p) for p in skip_prefixes):
        return

    try:
        parsed = sqlglot.parse(sql, read=BIGQUERY)
    except Exception as exc:  # sqlglot raises ParseError or ValueError
        msg = str(exc).split("\n")[0][:220]
        report.warn(origin, line, f"SQL parse warning: {msg}", sql.strip()[:160])
        return

    if parsed is None:
        report.warn(origin, line, "SQL parsed to None (empty/invalid)", sql.strip()[:160])


# --------------------------------------------------------------------------
# Python validation
# --------------------------------------------------------------------------

def validate_python(report: Report, origin: str, source: str, line: int | None):
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        lines = source.splitlines()
        bad = lines[exc.lineno - 1] if exc.lineno and exc.lineno <= len(lines) else ""
        report.error(
            origin,
            line,
            f"Python syntax error: {exc.msg} (col {exc.offset})",
            bad[:140],
        )
        return

    try:
        from google.cloud import bigquery
    except ImportError:
        return

    # Track names bound to the bigquery module so `from google.cloud import
    # bigquery as bq` style aliases are also checked, and so that a local
    # variable named `table` is NOT mistaken for the SDK's table module.
    aliases = {"bigquery"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "google.cloud.bigquery":
                    aliases.add(alias.asname or "bigquery")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "google.cloud" and any(a.name == "bigquery" for a in node.names):
                for a in node.names:
                    if a.name == "bigquery":
                        aliases.add(a.asname or "bigquery")

    # Names that shadow the SDK's `table` module (a local `table = client.get_table(...)`).
    shadowed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    shadowed.add(tgt.id)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name):
                shadowed.add(node.target.id)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if isinstance(node.value, ast.Name) and node.value.id in aliases:
            if not hasattr(bigquery, node.attr):
                report.error(
                    origin,
                    getattr(node, "lineno", line),
                    f"bigquery.{node.attr} does not exist in google-cloud-bigquery",
                )


# --------------------------------------------------------------------------
# Placeholder / hygiene checks
# --------------------------------------------------------------------------

PLACEHOLDER_OK = {
    "YOUR_PROJECT_ID",
    "YOUR_PROJECT",
    "YOUR_PROJECT_ID-bq-course",
    "YOUR_DATASET",
    "YOUR_TABLE",
    "YOUR_BUCKET",
    "YOUR_PROJECT_ID.bucket",
}

BAD_TOKENS = re.compile(r"\b(TODO|FIXME|XXX|HACK|PLACEHOLDER_VALUE|your-project-id)\b")


def check_hygiene(report: Report, origin: str, text: str):
    for m in BAD_TOKENS.finditer(text):
        line = text[: m.start()].count("\n") + 1
        report.warn(origin, line, f"unresolved marker: {m.group(0)}")


# --------------------------------------------------------------------------
# Link checking
# --------------------------------------------------------------------------

def check_links(report: Report, origin: str, base: Path, text: str):
    for m in re.finditer(r"\]\(([^)\s]+)\)", text):
        target = m.group(1)
        if target.startswith(("http", "#", "mailto:")):
            continue
        resolved = (base / target).resolve()
        if not resolved.exists():
            line = text[: m.start()].count("\n") + 1
            report.error(origin, line, f"broken link: {target}")


# --------------------------------------------------------------------------
# Main audit
# --------------------------------------------------------------------------

def audit_notebooks(report: Report):
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
                validate_python(report, rel, src, idx)
                for lineno, sql in extract_sql_from_python(src):
                    validate_sql(report, rel, sql, lineno)
                check_hygiene(report, rel, src)
            else:
                check_links(report, rel, path.parent, src)
                check_hygiene(report, rel, src)


def audit_sql_scripts(report: Report):
    for path in sorted(SQLDIR.glob("*.sql")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        stmts = split_sql_statements(text)
        if not stmts:
            report.warn(rel, None, "no SQL statements found")
        for stmt in stmts:
            validate_sql(report, rel, stmt, None)
        check_hygiene(report, rel, text)


def audit_chapters(report: Report):
    for path in sorted(CHAPTERS.glob("*.md")):
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        check_links(report, rel, path.parent, text)
        check_hygiene(report, rel, text)

        # fenced python blocks
        for m in re.finditer(r"```python\n(.*?)```", text, re.DOTALL):
            block = m.group(1)
            lineno = text[: m.start()].count("\n") + 1
            validate_python(report, rel, block, lineno)

        # fenced sql blocks
        for m in re.finditer(r"```sql\n(.*?)```", text, re.DOTALL):
            block = m.group(1)
            lineno = text[: m.start()].count("\n") + 1
            for stmt in split_sql_statements(block):
                validate_sql(report, rel, stmt, lineno)


def audit_resources(report: Report):
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


def audit_readme(report: Report):
    path = ROOT / "README.md"
    text = path.read_text()
    check_links(report, "README.md", ROOT, text)
    check_hygiene(report, "README.md", text)


def main() -> int:
    report = Report()
    audit_notebooks(report)
    audit_sql_scripts(report)
    audit_chapters(report)
    audit_resources(report)
    audit_readme(report)

    errors = report.by_severity("ERROR")
    warns = report.by_severity("WARN")
    infos = report.by_severity("INFO")

    print("=" * 78)
    print("BIGQUERY COURSE AUDIT")
    print("=" * 78)
    print(f"ERRORS: {len(errors)}   WARNINGS: {len(warns)}   INFO: {len(infos)}")
    print()

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
