"""Top-level smoke test: run `dbt parse` against dbt_project/.

Skips if `dbt` isn't installed.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conftest import dbt_project_root, run_dbt_parse  # noqa: E402

PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1] / "dbt_project"


def test_dbt_project_directory_exists():
    assert PROJECT_DIR.exists()
    assert (PROJECT_DIR / "dbt_project.yml").exists()
    assert (PROJECT_DIR / "profiles.yml").exists()
    assert (PROJECT_DIR / "packages.yml").exists()


def test_dbt_project_yml_has_required_fields():
    import yaml
    with (PROJECT_DIR / "dbt_project.yml").open() as f:
        yml = yaml.safe_load(f)
    assert yml["name"] == "dbt_snowflake_dbt"
    assert yml["profile"] == "dbt_snowflake_dbt"
    assert "models" in yml
    assert "vars" in yml


def test_dbt_parse_succeeds():
    """The shared dbt project should parse without errors."""
    proc = run_dbt_parse()
    if proc is None:
        pytest.skip("dbt not installed")
    if proc.returncode != 0:
        # Print stdout/stderr for debugging
        print("dbt parse stdout:", proc.stdout)
        print("dbt parse stderr:", proc.stderr)
    assert proc.returncode == 0, "dbt parse failed"


def test_models_directory_has_staging_and_marts():
    models = PROJECT_DIR / "models"
    assert (models / "staging").exists()
    assert (models / "marts").exists()


def test_staging_has_sources_yml():
    assert (PROJECT_DIR / "models" / "staging" / "_sources.yml").exists()


def test_marts_has_4_yml_files():
    """In dbt 1.12, each model must be declared in only one schema.yml
    file. We've split concerns across 4 files:
      - _access.yml (access + group + grants)
      - _contracts.yml (column-level test docs)
      - _grants.yml (project-wide grant defaults)
      - _versions.yml (versioned model declarations)
    """
    marts = PROJECT_DIR / "models" / "marts"
    ymls = list(marts.glob("*.yml"))
    assert len(ymls) >= 4, f"expected 4+ .yml files in marts, found {len(ymls)}"


def test_macros_directory_has_3_files():
    macros = PROJECT_DIR / "macros"
    files = list(macros.glob("*.sql"))
    assert len(files) >= 3, f"expected 3+ macros, found {len(files)}"


def test_snapshots_directory_has_snapshot():
    snapshots = PROJECT_DIR / "snapshots"
    files = list(snapshots.glob("*.sql"))
    assert len(files) >= 1


def test_seeds_directory_has_csv():
    seeds = PROJECT_DIR / "seeds"
    csvs = list(seeds.glob("*.csv"))
    assert len(csvs) >= 1


def test_author_signature_in_dbt_project():
    """The dbt_project README + dbt_project.yml must have the author line."""
    for fname in ("README.md", "dbt_project.yml", "profiles.yml", "packages.yml"):
        path = PROJECT_DIR / fname
        assert path.exists()
        content = path.read_text()
        assert "Prem Vishnoi" in content, f"author missing in {fname}"
        assert "pvishnoi@avilx.com" in content, f"email missing in {fname}"
        assert "pvilx.com" not in content, f"typo in {fname}"
