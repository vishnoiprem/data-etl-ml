"""Tests for 13_section/code/contracts_demo.yml."""
from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

YAML_PATH = pathlib.Path(__file__).resolve().parent / "contracts_demo.yml"


def _yml() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def test_file_exists_and_valid_yaml():
    assert YAML_PATH.exists()
    assert _yml()["version"] == 2


def test_enforces_contract():
    yml = _yml()
    models = yml["models"]
    assert any(m.get("config", {}).get("contract", {}).get("enforced") for m in models)


def test_declares_column_data_types():
    yml = _yml()
    tx_model = next(m for m in yml["models"] if m["name"] == "transactions_demo")
    for col in tx_model["columns"]:
        assert "data_type" in col, f"column {col['name']!r} missing data_type"


def test_has_not_null_and_unique_on_pk():
    yml = _yml()
    tx_model = next(m for m in yml["models"] if m["name"] == "transactions_demo")
    pk = next(c for c in tx_model["columns"] if c["name"] == "tx_hash")
    assert "not_null" in pk["tests"]
    assert "unique" in pk["tests"]


def test_accepted_values_test_present():
    yml = _yml()
    tx_model = next(m for m in yml["models"] if m["name"] == "transactions_demo")
    cat_col = next(c for c in tx_model["columns"] if c["name"] == "tx_category")
    test = cat_col["tests"][0]
    assert "accepted_values" in test
    assert "stablecoin_transfer" in test["accepted_values"]["values"]


def test_author_signature():
    s = YAML_PATH.read_text()
    assert "Prem Vishnoi" in s
    assert "pvishnoi@avilx.com" in s
    assert "pvilx.com" not in s
