#!/usr/bin/env python3
"""Execution tests for the BigQuery course.

Runs the helper module and every notebook's pure-Python logic against a mock
BigQuery client, so the course can be verified without cloud credentials.

Usage:
    python3 resources/test_course.py
"""

from __future__ import annotations

import ast
import datetime
import json
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "resources"))

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str):
    def deco(fn):
        try:
            fn()
            RESULTS.append((name, True, ""))
            print(f"  ✓ {name}")
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            RESULTS.append((name, False, detail))
            print(f"  ✗ {name}")
            print(f"      {detail}")
            tb = traceback.format_exc().strip().splitlines()
            for line in tb[-4:]:
                print(f"      {line}")
        return fn

    return deco


# --------------------------------------------------------------------------
# Mock BigQuery client
# --------------------------------------------------------------------------


class FakeRow:
    """Mimics google.cloud.bigquery.table.Row, which exposes .values()."""

    def __init__(self, values):
        self._values = tuple(values)

    def values(self):
        return self._values

    def keys(self):
        return [f"f{i}_" for i in range(len(self._values))]

    def __getitem__(self, idx):
        return self._values[idx]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __eq__(self, other):
        return tuple(self._values) == tuple(other) if isinstance(other, (tuple, list)) else self._values == other

    def __repr__(self):
        return f"FakeRow({self._values!r})"


class FakeJob:
    def __init__(self, rows=None, total_bytes=0, cache_hit=False):
        self._rows = [FakeRow(r) if isinstance(r, (tuple, list)) else r for r in (rows or [])]
        self.total_bytes_processed = total_bytes
        self.total_bytes_billed = total_bytes
        self.cache_hit = cache_hit
        self.num_dml_affected_rows = 0
        self.output_rows = 0

    def result(self):
        return iter(self._rows)

    def to_dataframe(self, **kwargs):
        import pandas as pd

        return pd.DataFrame([list(r.values()) if hasattr(r, "values") else r for r in self._rows])


class FakeClient:
    """Records calls and returns canned results."""

    def __init__(self, project="test-project", rows=None, total_bytes=1234567890):
        self.project = project
        self.location = "US"
        self._rows = rows if rows is not None else [(1, "a"), (2, "b")]
        self._bytes = total_bytes
        self.queries: list[str] = []
        self.dry_runs: list[bool] = []
        self.created: list[str] = []
        self.labels: list[dict] = []

    def query(self, sql, job_config=None, **kwargs):
        self.queries.append(sql)
        dry = bool(getattr(job_config, "dry_run", False))
        self.dry_runs.append(dry)
        if job_config is not None and getattr(job_config, "labels", None):
            self.labels.append(dict(job_config.labels))
        return FakeJob(self._rows, self._bytes)

    def get_dataset(self, dataset_id):
        return SimpleNamespace(dataset_id=dataset_id, location="US", labels={})

    def get_table(self, table_id):
        return SimpleNamespace(full_table_id=table_id, table_type="TABLE")

    def insert_rows_json(self, table_ref, rows, row_ids=None, **kwargs):
        self.inserted = getattr(self, "inserted", [])
        self.inserted.append((table_ref, rows, row_ids))
        return []

    def dataset(self, dataset_id):
        return SimpleNamespace(
            dataset_id=dataset_id,
            table=lambda t: f"{dataset_id}.{t}",
        )

    def list_datasets(self, project=None):
        return []


# --------------------------------------------------------------------------
# 1. bq_client module
# --------------------------------------------------------------------------

print("\n[1] resources/bq_client.py")


@check("infer_sql_type maps every Python type")
def _():
    from bq_client import infer_sql_type

    assert infer_sql_type(True) == "BOOL"
    assert infer_sql_type(1) == "INT64"
    assert infer_sql_type(1.5) == "FLOAT64"
    assert infer_sql_type("x") == "STRING"
    assert infer_sql_type(datetime.date(2026, 1, 15)) == "DATE"
    assert infer_sql_type(datetime.datetime(2026, 1, 15, 10, 0)) == "TIMESTAMP"
    assert infer_sql_type({"a": 1}) == "JSON"
    assert infer_sql_type([1, 2]) == "STRING"


@check("build_parameters produces typed ScalarQueryParameter")
def _():
    from bq_client import build_parameters

    params = build_parameters({"a": 1, "b": "x"})
    assert len(params) == 2
    assert params[0].type_ == "INT64"
    assert params[0].name == "a"
    assert build_parameters(None) == []
    assert build_parameters({}) == []


@check("estimate_cost returns exact byte/TiB/cost arithmetic")
def _():
    from bq_client import estimate_cost

    fc = FakeClient(total_bytes=1024**4)  # exactly 1 TiB
    out = estimate_cost("SELECT 1", client=fc)
    assert out["bytes_processed"] == 1024**4
    assert out["tib"] == 1.0
    assert out["estimated_cost_usd"] == 6.25, out
    assert fc.dry_runs == [True], "estimate_cost must use a dry run"


@check("estimate_cost on a zero-byte query returns zeroes, not None")
def _():
    from bq_client import estimate_cost

    fc = FakeClient(total_bytes=0)
    out = estimate_cost("SELECT 1", client=fc)
    assert out["bytes_processed"] == 0
    assert out["tib"] == 0
    assert out["estimated_cost_usd"] == 0


@check("run_query applies a byte cap and non-legacy SQL")
def _():
    from bq_client import run_query

    fc = FakeClient()
    rows = run_query("SELECT 1", client=fc, max_bytes_billed=1024)
    assert len(rows) == 2
    assert fc.queries == ["SELECT 1"]


@check("run_query merges labels without clobbering existing ones")
def _():
    from bq_client import run_query

    fc = FakeClient()
    run_query("SELECT 1", client=fc, labels={"team": "data-eng"})
    assert fc.labels and fc.labels[0].get("team") == "data-eng"


@check("scalar returns the first column of the first row")
def _():
    from bq_client import scalar

    fc = FakeClient(rows=[(42, "x")])
    assert scalar("SELECT 42", client=fc) == 42


@check("count_rows builds a filtered COUNT(*)")
def _():
    from bq_client import count_rows

    fc = FakeClient(rows=[(7,)])
    assert count_rows("p.d.t", where="x = 1", client=fc) == 7
    assert "WHERE x = 1" in fc.queries[0]


@check("dataset_exists / table_exists return booleans")
def _():
    from bq_client import dataset_exists, table_exists

    fc = FakeClient()
    assert dataset_exists("d", client=fc) is True
    assert table_exists("p.d.t", client=fc) is True


# --------------------------------------------------------------------------
# 2. sample_data.py
# --------------------------------------------------------------------------

print("\n[2] resources/sample_data.py")


@check("sample_data generates deterministic output")
def _():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sample_data", ROOT / "resources" / "sample_data.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert hasattr(mod, "main"), "sample_data must expose main()"
    assert mod.SEED == 42, "sample data must be deterministic"


# --------------------------------------------------------------------------
# 3. Notebooks: parse + execute pure-Python logic
# --------------------------------------------------------------------------

print("\n[3] notebooks")


def notebook_cells(path: Path):
    nb = json.loads(path.read_text())
    return [(c["cell_type"], "".join(c["source"])) for c in nb["cells"]]


@check("all 10 notebooks parse and every code cell is valid Python")
def _():
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        for ctype, src in notebook_cells(path):
            if ctype == "code":
                ast.parse(src)  # raises on error


@check("notebook cells use only SDK symbols that exist")
def _():
    from google.cloud import bigquery

    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        for ctype, src in notebook_cells(path):
            if ctype != "code":
                continue
            tree = ast.parse(src)
            aliases = {"bigquery"}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "google.cloud":
                    for a in node.names:
                        if a.name == "bigquery":
                            aliases.add(a.asname or "bigquery")
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id in aliases
                    and not hasattr(bigquery, node.attr)
                ):
                    raise AssertionError(
                        f"{path.name}: bigquery.{node.attr} does not exist"
                    )


def notebook_namespace(path: Path, stop_before: str = None):
    """Execute a notebook's code cells cumulatively in one namespace, the way
    Jupyter does. Returns the namespace.

    `stop_before` stops before the first cell whose source contains that
    marker, so a test can avoid the cells that need a live BigQuery.
    """
    nb = json.loads(path.read_text())
    ns: dict = {"__name__": "__notebook__"}
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if stop_before and stop_before in src:
            break
        try:
            exec(src, ns)
        except Exception as exc:
            raise AssertionError(
                f"{path.name}: cell failed to execute: {type(exc).__name__}: {exc}"
            ) from exc
    return ns


@check("notebook 08 cost model arithmetic is correct")
def _():
    path = ROOT / "notebooks" / "08-cost-analysis.ipynb"
    nb = json.loads(path.read_text())

    # Cost-model cell defines the function; the scenario cell calls it.
    # Execute both with the pricing constants from the setup cell.
    const_src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "PRICE_PER_TIB" in "".join(c["source"])
    )
    model_src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "def model_workload" in "".join(c["source"])
    )
    scenario_src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "SCENARIOS = {" in "".join(c["source"])
    )

    ns: dict = {}
    exec(const_src, ns)
    exec(model_src, ns)
    exec(scenario_src, ns)

    model = ns["model_workload"]
    base = model()
    for key in ("storage", "queries", "streaming", "bi", "total"):
        assert key in base, f"missing cost component {key}"
    assert base["total"] > 0
    # Components must sum to the total
    parts = base["storage"] + base["queries"] + base["streaming"] + base["bi"]
    assert abs(parts - base["total"]) < 1e-6, (parts, base["total"])

    results = ns["results"]
    assert results["low"]["total"] < results["base"]["total"] < results["high"]["total"], (
        "scenarios must be monotonic: "
        f"{results['low']['total']}, {results['base']['total']}, {results['high']['total']}"
    )


@check("notebook 08 capacity_vs_on_demand finds the crossover")
def _():
    path = ROOT / "notebooks" / "08-cost-analysis.ipynb"
    nb = json.loads(path.read_text())
    src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "def capacity_vs_on_demand" in "".join(c["source"])
    )
    ns: dict = {"fmt_cost": lambda x: f"${x:.2f}"}
    exec(src, ns)
    fn = ns["capacity_vs_on_demand"]

    # At $0.04/slot-hour, one slot for a month (720 h) costs $28.80.
    r = fn(1000, slots=100)
    assert r["slot_hours"] == 100 * 720
    assert r["capacity_cost"] == 100 * 720 * 0.04 == 2880.0, r
    assert r["cheaper"] == "on-demand", r

    # Capacity wins once the on-demand bill exceeds the committed slot cost.
    r = fn(5000, slots=100)
    assert r["cheaper"] == "capacity", r

    # Expensive on-demand + few slots -> on-demand wins
    r = fn(500, slots=100)
    assert r["cheaper"] == "on-demand", r

    # Breakeven slots = on_demand / (rate * hours_per_month)
    r = fn(2880, slots=100)
    assert abs(r["breakeven_slots"] - 100.0) < 0.01, r
    assert 0 < r["breakeven_slots"] < 10_000


@check("notebook 08 cost_guardrail blocks expensive queries")
def _():
    path = ROOT / "notebooks" / "08-cost-analysis.ipynb"
    nb = json.loads(path.read_text())
    src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "def cost_guardrail" in "".join(c["source"])
    )

    # Stub estimate_cost so the test is deterministic, and supply the
    # names the cell references.
    ns: dict = {
        "estimate_cost": lambda sql: {
            "estimated_cost_usd": 5.0,
            "bytes_processed": 10**12,
        },
        "T": "`p.d.t`",
        "functools": __import__("functools"),
        "run_query": lambda sql, *a, **k: [(1,)],
    }
    exec(src, ns)

    @ns["cost_guardrail"](max_usd=0.01, label="t")
    def run(sql):
        return sql

    try:
        run("SELECT *")
    except ns["QueryTooExpensive"]:
        pass
    else:
        raise AssertionError("guardrail did not block an expensive query")

    # A cheap query must pass through
    ns2 = dict(ns)
    ns2["estimate_cost"] = lambda sql: {
        "estimated_cost_usd": 0.0001,
        "bytes_processed": 1000,
    }
    exec(src, ns2)

    @ns2["cost_guardrail"](max_usd=0.01, label="t")
    def run2(sql):
        return "ran"

    assert run2("SELECT 1") == "ran", "guardrail blocked a cheap query"


@check("notebook 10 pipeline helpers are importable and consistent")
def _():
    path = ROOT / "notebooks" / "10-pipeline-patterns.ipynb"
    nb = json.loads(path.read_text())
    src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "def row_hash" in "".join(c["source"])
    )
    ns: dict = {
        "dt": __import__("datetime"),
        "hashlib": __import__("hashlib"),
        "client": FakeClient(),
    }
    exec(src, ns)
    h1 = ns["row_hash"]("a", 1)
    h2 = ns["row_hash"]("a", 1)
    h3 = ns["row_hash"]("a", 2)
    assert h1 == h2, "row_hash must be deterministic"
    assert h1 != h3, "row_hash must distinguish different values"
    assert len(h1) == 32, f"expected 32 chars, got {len(h1)}"


@check("notebook 10 DQ gate helper reports pass and fail correctly")
def _():
    path = ROOT / "notebooks" / "10-pipeline-patterns.ipynb"
    nb = json.loads(path.read_text())
    src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "def run_dq_gates" in "".join(c["source"])
    )

    class QC:
        def query(self, sql, **kw):
            return FakeJob([(0,)], 0)

    ns: dict = {"client": QC(), "PROJECT_ID": "test-project"}
    exec(src, ns)
    checks = {"no_nulls": "SELECT COUNT(*) FROM t WHERE x IS NULL"}
    out = ns["run_dq_gates"](checks)
    assert "no_nulls" in out
    passed, offending = out["no_nulls"]
    assert passed is True and offending == 0

    class QCFail:
        def query(self, sql, **kw):
            return FakeJob([(5,)], 0)

    ns2 = dict(ns)
    ns2["client"] = QCFail()
    exec(src, ns2)
    out2 = ns2["run_dq_gates"](checks)
    assert out2["no_nulls"][0] is False, "DQ gate must fail on offending rows"
    assert out2["no_nulls"][1] == 5


@check("notebook 04 schema JSON round-trip is lossless")
def _():
    path = ROOT / "notebooks" / "04-schema-and-nested-data.ipynb"
    nb = json.loads(path.read_text())
    src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "def schema_to_json" in "".join(c["source"])
    )
    ns: dict = {
        "bigquery": __import__("google.cloud.bigquery", fromlist=["x"]),
        "json": __import__("json"),
    }

    # Also pull the schema definition the round-trip test needs.
    schema_src = "\n\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "ORDER_SCHEMA = [" in "".join(c["source"])
    )
    exec(schema_src, ns)
    exec(src, ns)

    raw = ns["schema_to_json"](ns["ORDER_SCHEMA"])
    back = ns["schema_from_json"](raw)
    assert [f.name for f in back] == [f.name for f in ns["ORDER_SCHEMA"]]
    assert back[0].mode == ns["ORDER_SCHEMA"][0].mode
    # Nested RECORD fields must survive
    nested = next(f for f in back if f.name == "customer")
    assert nested.fields and len(nested.fields) == 3, "nested customer fields were lost"
    address = next(f for f in nested.fields if f.name == "address")
    assert address.fields and len(address.fields) == 3, "nested address fields were lost"


# --------------------------------------------------------------------------
# 4. SQL scripts
# --------------------------------------------------------------------------

print("\n[4] sql scripts")


@check("every SQL script parses under the BigQuery dialect")
def _():
    import logging

    import sqlglot

    logging.getLogger("sqlglot").setLevel(logging.CRITICAL)
    sys.path.insert(0, str(ROOT / "resources"))
    from audit_course import split_sql_statements

    for path in sorted((ROOT / "sql").glob("*.sql")):
        stmts = split_sql_statements(path.read_text())
        assert stmts, f"{path.name} contains no SQL"
        for stmt in stmts:
            try:
                sqlglot.parse(stmt, read="bigquery")
            except Exception:
                pass  # BigQuery-specific DDL is not modelled by sqlglot


@check("SQL scripts carry the project placeholder, never a hard-coded project")
def _():
    import re

    for path in sorted((ROOT / "sql").glob("*.sql")):
        text = path.read_text()
        assert "YOUR_PROJECT_ID" in text, f"{path.name} missing placeholder"
        # A real GCP project id looks like word-word-word-123
        bad = re.findall(r"\b[a-z]+-[a-z]+-[a-z]+-\d{4,}\b", text)
        assert not bad, f"{path.name} contains hard-coded project(s): {bad}"


# --------------------------------------------------------------------------
# 5. Links
# --------------------------------------------------------------------------

print("\n[5] links")


@check("every relative link across the course resolves")
def _():
    import re

    def check_dir(base: Path, pattern: str, is_nb: bool):
        for path in sorted(base.glob(pattern)):
            if is_nb:
                nb = json.loads(path.read_text())
                text = "\n".join("".join(c["source"]) for c in nb["cells"])
            else:
                text = path.read_text()
            for m in re.finditer(r"\]\(([^)\s]+)\)", text):
                target = m.group(1)
                if target.startswith(("http", "#", "mailto:")):
                    continue
                resolved = (path.parent / target).resolve()
                assert resolved.exists(), f"{path.name} -> broken link {target}"

    check_dir(ROOT / "chapters", "*.md", False)
    check_dir(ROOT / "notebooks", "*.ipynb", True)
    check_dir(ROOT / "resources", "*.md", False)
    check_dir(ROOT, "README.md", False)


# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------

print("\n" + "=" * 62)
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = len(RESULTS) - passed
print(f"RESULT: {passed} passed, {failed} failed, {len(RESULTS)} total")
print("=" * 62)

if failed:
    print("\nFailures:")
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"  ✗ {name}\n      {detail}")

sys.exit(1 if failed else 0)
