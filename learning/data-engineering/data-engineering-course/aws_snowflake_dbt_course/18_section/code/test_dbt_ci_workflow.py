"""Tests for 18_section/code/dbt_ci_workflow.yml."""
from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

YAML_PATH = pathlib.Path(__file__).resolve().parent / "dbt_ci_workflow.yml"


def _yml() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def test_file_exists_and_valid_yaml():
    assert YAML_PATH.exists()
    yml = _yml()
    assert yml["name"] == "dbt CI"


def test_triggers_on_pull_request():
    yml = _yml()
    on = yml[True]
    assert "pull_request" in on


def test_uses_state_modified_selector():
    """Slim CI must use the state:modified+ selector."""
    s = YAML_PATH.read_text()
    assert "state:modified+" in s


def test_uses_defer_flag():
    """Slim CI must use --defer to share prod tables for unmodified models."""
    s = YAML_PATH.read_text()
    assert "--defer" in s


def test_has_build_job():
    yml = _yml()
    assert "dbt_build" in yml["jobs"]


def test_has_deploy_job():
    yml = _yml()
    assert "dbt_deploy" in yml["jobs"]


def test_deploy_only_on_main():
    yml = _yml()
    deploy = yml["jobs"]["dbt_deploy"]
    cond = deploy.get("if", "")
    assert "main" in cond


def test_author_signature():
    s = YAML_PATH.read_text()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
