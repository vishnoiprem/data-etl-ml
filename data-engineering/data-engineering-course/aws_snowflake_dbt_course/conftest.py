"""Shared test fixtures + helpers for the dbt + Snowflake course.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Mirrors the patterns from `aws_snowflake_course/conftest.py`:
  - `strip_line_comments(sql)`       - strip `--` line comments from SQL
  - `parse_sql_statements(sql)`      - split a SQL script into statements
  - `FakeCursor`, `FakeConnection`   - record SQL without a live Snowflake

Adds dbt-specific helpers:
  - `render_jinja(text, context)`    — render a Jinja template with mock
                                       dbt context (ref, source, var, this)
  - `dbt_project_root()`             — path to the shared dbt_project/
  - `run_dbt_parse()`                — run `dbt parse` smoke test
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable

import pytest

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

HERE = pathlib.Path(__file__).resolve().parent
DBT_PROJECT = HERE / "dbt_project"


def dbt_project_root() -> pathlib.Path:
    """Return the absolute path to the shared dbt_project/."""
    return DBT_PROJECT


# ---------------------------------------------------------------------------
# SQL helpers (mirror of aws_snowflake_course/conftest.py)
# ---------------------------------------------------------------------------

_LINE_COMMENT_RE = re.compile(r"--[^\n]*")


def strip_line_comments(sql: str) -> str:
    """Remove `--` line comments from a SQL script. Preserves newlines
    so line-based test heuristics (CREATE statement scanning) still
    work, but every `--` comment becomes a blank line.
    """
    return _LINE_COMMENT_RE.sub("", sql)


def parse_sql_statements(sql: str) -> list[str]:
    """Split a (possibly multi-statement) SQL script into a list of
    individual statements, after stripping line comments and dropping
    empty statements.
    """
    stripped = strip_line_comments(sql)
    return [s.strip() for s in stripped.split(";") if s.strip()]


# ---------------------------------------------------------------------------
# Fake cursor / connection — for tests that need to *record* SQL without
# actually executing anything against Snowflake.
# ---------------------------------------------------------------------------

@dataclass
class FakeCursor:
    executed: list[tuple[str, tuple]] = field(default_factory=list)
    description: tuple = ()
    rowcount: int = 0

    def execute(self, sql: str, params: tuple = ()) -> "FakeCursor":
        self.executed.append((sql, params))
        return self

    def executemany(self, sql: str, seq: Iterable[tuple]) -> "FakeCursor":
        for p in seq:
            self.execute(sql, p)
        return self

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def close(self) -> None:
        pass


@dataclass
class FakeConnection:
    cursor: FakeCursor = field(default_factory=FakeCursor)
    closed: bool = False

    def cursor(self_):  # noqa: N805
        return self_.cursor

    def close(self_) -> None:  # noqa: N805
        self_.closed = True


def make_fake_conn() -> FakeConnection:
    return FakeConnection()


def executed_contains(needle: str, cursor: FakeCursor) -> bool:
    return any(needle.lower() in sql.lower() for sql, _ in cursor.executed)


@pytest.fixture
def fake_conn() -> FakeConnection:
    return make_fake_conn()


# ---------------------------------------------------------------------------
# dbt helpers
# ---------------------------------------------------------------------------

class _MockDbtContext:
    """A minimal stand-in for the dbt runtime context. Templates can
    call `ref('model')`, `source('schema','table')`, `var('foo')`,
    `this`, `is_incremental()`, etc.
    """

    def __init__(self, project_name: str = "dbt_snowflake_dbt") -> None:
        self.project_name = project_name
        self._refs: dict[str, str] = {}
        self._sources: dict[tuple[str, str], str] = {}
        self._vars: dict[str, Any] = {}
        self._is_incremental_override: bool | None = None

    # ref / source return a Relation-like object with .identifier
    def ref(self, *names: str) -> "_Relation":
        name = "__".join(names)
        rendered = self._refs.get(name, f"raw_{name}")
        return _Relation(database="DB", schema="public", identifier=rendered)

    def source(self, schema: str, table: str) -> "_Relation":
        rendered = self._sources.get((schema, table), f"{schema}_{table}")
        return _Relation(database="DB", schema="public", identifier=rendered)

    def var(self, name: str, default: Any = None) -> Any:
        return self._vars.get(name, default)

    def config(self, **kwargs: Any) -> dict[str, Any]:
        return dict(kwargs)

    # `this` inside a model resolves to the model's own relation
    @property
    def this(self) -> "_Relation":
        return _Relation(database="DB", schema="public", identifier="this_table")

    def is_incremental(self) -> bool:
        if self._is_incremental_override is not None:
            return self._is_incremental_override
        return True


@dataclass
class _Relation:
    database: str
    schema: str
    identifier: str

    def __str__(self) -> str:
        return f"{self.database}.{self.schema}.{self.identifier}"


def render_jinja(text: str, context: dict | None = None) -> str:
    """Render a Jinja template with a mock dbt context.

    `context` may include:
      - `refs`: dict[str,str]            — maps model_name -> rendered name
      - `sources`: dict[(schema,table)]  — maps source -> rendered
      - `vars`: dict[str, Any]           — template variables
      - `is_incremental`: bool           — override is_incremental() result

    Strips dbt-specific block tags ({% test %}, {% snapshot %},
    {% materialization %}, {% macro %}) before rendering, so the
    file's other Jinja constructs (ref, source, var, config, this,
    is_incremental, {% if %}, {% for %}, {{ }}) render correctly.
    """
    import re

    import jinja2

    # Strip dbt-specific block tags (preserving their bodies, so the
    # body is still validated for syntax errors like `{{ ref() }}`).
    text = re.sub(
        r"\{%-?\s*(test|snapshot|materialization|macro)\s+[^%]*?-?%\}",
        "",
        text,
    )
    text = re.sub(
        r"\{%-?\s*end(test|snapshot|materialization|macro)\s*-?%\}",
        "",
        text,
    )

    env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        undefined=jinja2.ChainableUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    ctx = _MockDbtContext()
    if context:
        ctx._refs.update(context.get("refs", {}))
        ctx._sources.update(context.get("sources", {}))
        ctx._vars.update(context.get("vars", {}))
        if "is_incremental" in context:
            ctx._is_incremental_override = context["is_incremental"]

    template = env.from_string(text)
    return template.render(
        ref=ctx.ref,
        source=ctx.source,
        var=ctx.var,
        config=ctx.config,
        this=ctx.this,
        is_incremental=ctx.is_incremental,
    )


def run_dbt_parse() -> subprocess.CompletedProcess | None:
    """Run `dbt parse` against the shared dbt_project/ as a smoke test.

    Returns the CompletedProcess, or `None` if `dbt` isn't installed
    (in which case callers should `pytest.skip`).
    """
    if shutil.which("dbt") is None:
        return None

    return subprocess.run(
        [
            "dbt",
            "parse",
            "--project-dir",
            str(DBT_PROJECT),
            "--profiles-dir",
            str(DBT_PROJECT),
            "--no-version-check",
            "--target",
            "mock",
        ],
        capture_output=True,
        text=True,
        cwd=str(DBT_PROJECT),
    )


def load_manifest() -> dict | None:
    """Load `dbt_project/target/manifest.json` after a `dbt parse` run.

    Returns None if the manifest doesn't exist (i.e., dbt parse
    hasn't been run yet).
    """
    manifest_path = DBT_PROJECT / "target" / "manifest.json"
    if not manifest_path.exists():
        return None
    with manifest_path.open() as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def dbt_manifest() -> dict | None:
    """Session-scoped fixture: runs `dbt parse` once and returns the
    manifest, so individual tests can assert on the parsed project
    state without re-running dbt.
    """
    proc = run_dbt_parse()
    if proc is not None and proc.returncode != 0:
        # Don't fail here — let individual tests decide whether the
        # parse failure is a problem they're testing for.
        pass
    return load_manifest()
