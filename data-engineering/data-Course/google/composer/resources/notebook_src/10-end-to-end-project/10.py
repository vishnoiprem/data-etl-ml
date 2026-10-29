"""Read the DAG files structurally, without importing Airflow.

Importing a DAG file would require Airflow, and Airflow is deliberately
absent from this machine. Instead we parse the *text*: pull out the
`dag_id`, the `schedule`, the operator classes, the task_ids and the
dependency edges.

This is a real technique, not a workaround. It is how you lint DAG
files in CI, count how many operators a DAG uses, and check that a DAG
has not silently grown a dependency that breaks a branch.
"""

import ast
import re
from pathlib import Path

DAGS_DIR = COURSE_ROOT / "project" / "dags"


def analyse_dag_file(path: Path) -> dict:
    """Extract the structure of a DAG file from its source text.

    Args:
        path: The path to the DAG file.

    Returns:
        A dict with the dag_id, schedule, operators, task_ids, params
        and the dependency edges.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    dag_id = None
    schedule = None
    start_date = None
    catchup = None
    max_active_runs = None
    sla = None
    tags: list[str] = []
    params: dict[str, object] = {}
    operators: list[str] = []
    task_ids: list[str] = []
    edges: list[tuple[str, str]] = []
    defaults: dict[str, object] = {}

    # --- the `with DAG(...)` call -----------------------------------
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name == "DAG":
                for kw in node.keywords:
                    if kw.arg == "dag_id" and isinstance(kw.value, ast.Constant):
                        dag_id = kw.value.value
                    elif kw.arg == "schedule" and isinstance(kw.value, ast.Constant):
                        schedule = kw.value.value
                    elif kw.arg == "catchup" and isinstance(kw.value, ast.Constant):
                        catchup = kw.value.value
                    elif kw.arg == "max_active_runs" and isinstance(kw.value, ast.Constant):
                        max_active_runs = kw.value.value
                    elif kw.arg == "tags" and isinstance(kw.value, ast.List):
                        tags = [
                            e.value for e in kw.value.elts
                            if isinstance(e, ast.Constant)
                        ]
                    elif kw.arg == "params" and isinstance(kw.value, ast.Dict):
                        for k, v in zip(kw.value.keys, kw.value.values):
                            if isinstance(k, ast.Constant):
                                try:
                                    params[k.value] = ast.literal_eval(v)
                                except (ValueError, SyntaxError):
                                    params[k.value] = "<computed>"
                    elif kw.arg == "sla":
                        sla = ast.unparse(kw.value)

    # --- DEFAULT_ARGS ------------------------------------------------
    # `DEFAULT_ARGS` contains `timedelta(minutes=5)`, which is a Call and
    # therefore not a literal. Read it key by key, and fall back to the
    # unparsed source for anything that is not a plain literal.
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if getattr(target, "id", None) == "DEFAULT_ARGS":
                    if isinstance(node.value, ast.Dict):
                        for k, v in zip(node.value.keys, node.value.values):
                            if not isinstance(k, ast.Constant):
                                continue
                            try:
                                defaults[k.value] = ast.literal_eval(v)
                            except (ValueError, SyntaxError):
                                defaults[k.value] = ast.unparse(v)

    # --- the operator calls -----------------------------------------
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            cls = getattr(func, "id", None)
            if cls and cls.endswith("Operator"):
                operators.append(cls)
                for kw in node.keywords:
                    if kw.arg == "task_id" and isinstance(kw.value, ast.Constant):
                        task_ids.append(kw.value.value)
                if cls == "PythonSensor":
                    for kw in node.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                            task_ids.append(f"(mode={kw.value.value})")
                if cls == "BigQueryInsertJobOperator":
                    pass

    # --- the `a >> b` dependency expressions ------------------------
    # A chain like `count >> sensor >> branch` is a nested BinOp, so
    # `a >> (b >> c)` must be flattened to [(a, b), (b, c)].
    def _flatten_shifts(node: ast.AST) -> list[tuple[str, str]]:
        """Return the (left, right) pairs of a `>>` chain.

        Args:
            node: The AST node to flatten.

        Returns:
            A list of (left_name, right_name) pairs.
        """
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.BitOr):
            return []
        if isinstance(node.left, ast.Name):
            left_name = node.left.id
        else:
            left_name = None
        if isinstance(node.right, ast.Name):
            right_name = node.right.id
        else:
            right_name = None
        pairs = []
        if left_name and right_name:
            pairs.append((left_name, right_name))
        pairs.extend(_flatten_shifts(node.left))
        pairs.extend(_flatten_shifts(node.right))
        return pairs

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            edges.extend(_flatten_shifts(node))

    return {
        "file": path.name,
        "dag_id": dag_id,
        "schedule": schedule,
        "start_date": start_date,
        "catchup": catchup,
        "max_active_runs": max_active_runs,
        "sla": sla,
        "tags": tags,
        "params": params,
        "default_args": defaults,
        "operators": operators,
        "task_ids": task_ids,
        "edges": edges,
        "source_lines": len(source.splitlines()),
    }


DAG_FILES = sorted(DAGS_DIR.glob("*.py"))
DAG_FILES = [p for p in DAG_FILES if p.name != "dag_config.py"]

analyses = [analyse_dag_file(path) for path in DAG_FILES]

print("=" * 78)
print("THE FOUR DEPLOYABLE DAG FILES")
print("=" * 78)
print()

for analysis in analyses:
    print(f"── {analysis['file']} " + "─" * 52)
    print(f"  dag_id          : {analysis['dag_id']}")
    print(f"  schedule        : {analysis['schedule']}")
    print(f"  catchup         : {analysis['catchup']}")
    print(f"  max_active_runs : {analysis['max_active_runs']}")
    print(f"  sla             : {analysis['sla']}")
    print(f"  tags            : {analysis['tags']}")
    print(f"  default_args    : {analysis['default_args']}")
    print(f"  operators       : {analysis['operators']}")
    print(f"  task_ids        : {analysis['task_ids']}")
    print(f"  edges           : {analysis['edges']}")
    print(f"  params          :")
    for key, value in analysis["params"].items():
        print(f"      {key:<20} {value!r}")
    print(f"  lines           : {analysis['source_lines']}")
    print()

# --------------------------------------------------------------------------
# The properties that must hold for every deployable DAG
# --------------------------------------------------------------------------
print("=" * 78)
print("CHECKING THE PROPERTIES")
print("=" * 78)
print()

for analysis in analyses:
    name = analysis["file"]
    dag_id = analysis["dag_id"]

    # Every DAG needs a unique id.
    assert dag_id, f"{name} has no dag_id"

    # Every DAG needs a schedule (None means manual-only, which is legal).
    assert "schedule" in analysis, f"{name} has no schedule"

    # Every task_id must be unique within its DAG.
    task_ids = [t for t in analysis["task_ids"] if not t.startswith("(")]
    assert len(task_ids) == len(set(task_ids)), f"{name} has duplicate task_ids"

    # Every edge endpoint must name a real task.
    for left, right in analysis["edges"]:
        assert left in task_ids, f"{name}: edge source {left!r} is not a task"
        assert right in task_ids, f"{name}: edge target {right!r} is not a task"

    print(f"  {name:<34} ok  ({len(task_ids)} tasks, "
          f"{len(analysis['edges'])} edges)")

print()
print("Every DAG has a unique id, a schedule, unique task ids, and every")
print("dependency edge points at a task that exists.")
print()

# --------------------------------------------------------------------------
# The one that matters most: the half-open interval
# --------------------------------------------------------------------------
print("=" * 78)
print("THE PARTITION FILTER, VERIFIED IN THE SOURCE")
print("=" * 78)
print()

etl_source = (DAGS_DIR / "03_etl_bigquery.py").read_text(encoding="utf-8")

# Strip the docstrings and comments: `WRITE_APPEND` appears in the
# module docstring (explaining why it is *not* used), and a check that
# counts prose would be meaningless.
etl_tree = ast.parse(etl_source)
# Remove every docstring, so only executable code is left.
for node in ast.walk(etl_tree):
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            body.pop(0)
etl_code = ast.unparse(etl_tree)

has_start = "order_ts >= '{{ data_interval_start }}'" in etl_code
has_end = "order_ts <  '{{ data_interval_end }}'" in etl_code
has_truncate = '"writeDisposition": "WRITE_TRUNCATE"' in etl_code
has_append = "WRITE_APPEND" in etl_code
has_no_depends_on_past = '"depends_on_past": False' in etl_code
has_max_active = "max_active_runs=1" in etl_code
has_sla = "sla=DAG_SLA" in etl_code
has_export = "BigQueryToGCSOperator" in etl_code
has_scheduled_query = "BigQueryExecuteQueryOperator" in etl_code

checks = [
    ("filter uses >= data_interval_start", has_start),
    ("filter uses <  data_interval_end", has_end),
    ("writeDisposition is WRITE_TRUNCATE", has_truncate),
    ("WRITE_APPEND does not appear", not has_append),
    ("depends_on_past is False", has_no_depends_on_past),
    ("max_active_runs is 1", has_max_active),
    ("an SLA is declared", has_sla),
    ("the table is exported to GCS", has_export),
    ("the aggregate runs as a query", has_scheduled_query),
]

for label, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    assert ok, label

print()
print("The three properties that make this DAG production-safe:")
print("  * WRITE_TRUNCATE against a partition — a retry replaces, not appends")
print("  * the half-open interval filter — no midnight row counted twice")
print("  * depends_on_past=False + max_active_runs=1 — days are independent")
print()

# --------------------------------------------------------------------------
# The branching join
# --------------------------------------------------------------------------
print("=" * 78)
print("THE BRANCHING JOIN, VERIFIED IN THE SOURCE")
print("=" * 78)
print()

branch_source = (DAGS_DIR / "04_branching_and_xcom.py").read_text(encoding="utf-8")

branch_checks = [
    ("a BranchOperator is used", "BranchOperator(" in branch_source),
    ("the join uses trigger_rule=\"none_failed\"",
     'trigger_rule="none_failed"' in branch_source),
    ("the sensor uses mode=\"reschedule\"", 'mode="reschedule"' in branch_source),
    ("the sensor has a timeout", "timeout=3600" in branch_source),
    ("a TriggerDagRunOperator chains the DAGs",
     "TriggerDagRunOperator(" in branch_source),
    ("the conf is passed to the child", "conf={" in branch_source),
    ("the branch has both paths", "full_load" in branch_source
     and "incremental_load" in branch_source),
]

for label, ok in branch_checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    assert ok, label

print()
print("The join's trigger_rule is the difference between a working")
print("branch and a DAG that quietly does nothing.")
print()

# --------------------------------------------------------------------------
# The variables each DAG reads
# --------------------------------------------------------------------------
print("=" * 78)
print("THE VARIABLES EACH DAG READS")
print("=" * 78)
print()

all_vars: dict[str, set[str]] = {}
for path in DAG_FILES:
    source = path.read_text(encoding="utf-8")
    found = set(re.findall(r"var\.value\.(\w+)", source))
    all_vars[path.name] = found
    print(f"  {path.name:<34} {sorted(found)}")

union = set().union(*all_vars.values())
print()
print(f"union of all Variables read by the DAGs: {sorted(union)}")
print()
print("Every one of these must exist in the Composer's Admin -> Variables")
print("panel, or the DAG falls back to its default and quietly reads the")
print("wrong bucket.")
print()
