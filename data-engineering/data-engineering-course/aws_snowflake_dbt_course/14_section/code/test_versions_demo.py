"""Tests for 14_section/code/versions_demo.yml."""
from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

YAML_PATH = pathlib.Path(__file__).resolve().parent / "versions_demo.yml"


def _yml() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def test_file_exists_and_valid_yaml():
    assert YAML_PATH.exists()
    assert _yml()["version"] == 2


def test_declares_latest_version():
    yml = _yml()
    m = yml["models"][0]
    assert m.get("latest_version") == 2


def test_has_two_versions():
    yml = _yml()
    m = yml["models"][0]
    assert len(m["versions"]) == 2


def test_v1_has_deprecation_date():
    yml = _yml()
    m = yml["models"][0]
    v1 = next(v for v in m["versions"] if v["v"] == 1)
    # YAML parses ISO dates as datetime.date objects
    from datetime import date
    assert v1.get("deprecation_date") == date(2026, 12, 31)


def test_v1_has_bypass_version_check():
    yml = _yml()
    m = yml["models"][0]
    v1 = next(v for v in m["versions"] if v["v"] == 1)
    assert "bypass_version_check" in v1
    assert v1["bypass_version_check"] is False


def test_v2_enforces_contract():
    yml = _yml()
    m = yml["models"][0]
    v2 = next(v for v in m["versions"] if v["v"] == 2)
    assert v2["config"]["contract"]["enforced"] is True


def test_author_signature():
    s = YAML_PATH.read_text()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
