"""Tests for 17_section/code/state_selectors.yml."""
from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

YAML_PATH = pathlib.Path(__file__).resolve().parent / "state_selectors.yml"


def _yml() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def test_file_exists_and_valid_yaml():
    assert YAML_PATH.exists()
    yml = _yml()
    assert "selectors" in yml
    assert len(yml["selectors"]) >= 3


def test_uses_state_method():
    yml = _yml()
    all_methods = []
    for s in yml["selectors"]:
        for step in s.get("definition", []):
            if "method" in step:
                all_methods.append(step["method"])
            if "intersection" in step:
                for sub in step["intersection"]:
                    if "method" in sub:
                        all_methods.append(sub["method"])
    assert "state" in all_methods, "expected `state` method usage"


def test_uses_result_method():
    yml = _yml()
    all_methods = []
    for s in yml["selectors"]:
        for step in s.get("definition", []):
            if "intersection" in step:
                for sub in step["intersection"]:
                    if "method" in sub:
                        all_methods.append(sub["method"])
    assert "result" in all_methods, "expected `result` method usage"


def test_combines_state_and_result():
    yml = _yml()
    failed = next(s for s in yml["selectors"] if s["name"] == "failed_then_modified")
    intersection = failed["definition"][0]["intersection"]
    methods = [sub["method"] for sub in intersection]
    assert "state" in methods and "result" in methods


def test_uses_downstream_modifier():
    yml = _yml()
    ci = next(s for s in yml["selectors"] if s["name"] == "ci_modified")
    has_downstream = any(
        step.get("method") == "downstream" for step in ci["definition"]
    )
    assert has_downstream


def test_author_signature():
    s = YAML_PATH.read_text()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
