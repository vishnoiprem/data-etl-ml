"""
conftest.py — test configuration for the Composer course project.

The single most important thing this file does is make the test suite
runnable **without Airflow installed**. The pure-logic modules under
``project/core/`` import nothing from Airflow, so the tests exercise real
behaviour on a bare Python install.

If Airflow *is* installed, a couple of extra tests run — the DAG files
can then be imported and parsed, which is a genuinely useful check that
the DAGs are syntactically and semantically valid.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COURSE_ROOT = PROJECT_ROOT.parent
CORE_DIR = PROJECT_ROOT / "core"
DAGS_DIR = PROJECT_ROOT / "dags"
SAMPLE_DIR = COURSE_ROOT / "sample_data"

for _path in (str(CORE_DIR), str(DAGS_DIR), str(PROJECT_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def airflow_available() -> bool:
    """Return True when Airflow is importable.

    Returns:
        True if the airflow package can be imported.
    """
    try:
        import airflow  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    """Return the sample data directory.

    Returns:
        The path to ``sample_data``.
    """
    return SAMPLE_DIR


@pytest.fixture(scope="session")
def orders_csv(sample_dir: Path) -> Path:
    """Return the path to the sample orders CSV.

    Args:
        sample_dir: The sample data directory.

    Returns:
        The path to ``orders.csv``.
    """
    path = sample_dir / "orders.csv"
    if not path.exists():
        pytest.skip(
            "sample data not found. Generate it with:\n"
            "  python resources/sample_data.py --output-dir ./sample_data"
        )
    return path


@pytest.fixture(scope="session")
def order_lines(orders_csv: Path) -> list[str]:
    """Return the raw lines of the sample orders CSV.

    Args:
        orders_csv: The path to the orders CSV.

    Returns:
        The raw CSV lines.
    """
    return orders_csv.read_text(encoding="utf-8").splitlines()


@pytest.fixture(scope="session")
def context():
    """Return a fresh Jinja context for templating tests.

    Returns:
        The rendering context.
    """
    from templating import build_context

    return build_context(
        dag_id="test_dag",
        task_id="test_task",
        logical_date="2026-01-15",
        variables={"gcp_project_id": "demo-project", "source_bucket": "demo-bucket"},
        connections={
            "http_orders_api": {
                "conn_id": "http_orders_api",
                "host": "api.example.com",
                "extra": '{"timeout": 30}',
            }
        },
        params={"audience": "testers"},
    )
