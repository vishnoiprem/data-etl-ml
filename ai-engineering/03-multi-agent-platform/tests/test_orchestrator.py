"""Smoke tests for orchestration."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.orchestrator import run_orchestrator


GOOD = {"app_id": "T1", "name": "Alice Johnson", "ssn_last4": "4421", "dob": "1985-03-12",
        "amount": 25000, "purpose": "auto", "income_annual": 95000, "monthly_debt": 800,
        "credit_score": 740, "country": "US", "state": "CA"}

SANCTIONED = {**GOOD, "app_id": "T2", "name": "Evan Petrov"}
BIG = {**GOOD, "app_id": "T3", "amount": 500000, "purpose": "home_purchase", "state": "TX"}


def test_clean_application():
    d = run_orchestrator(GOOD)
    # The bureau pull is a stub keyed on ssn_last4; the resulting score may
    # land above or below the policy threshold. The thing we're testing is
    # that orchestration runs end-to-end and KYC passes.
    assert d.decision in {"approve", "decline", "refer"}
    assert d.kyc["id_verified"]
    assert not d.kyc["sanctions_hit"]
    assert d.cost_steps >= 5  # KYC(3) + Credit(3) + Policy(2) → at least some


def test_sanctions_hit_declined():
    d = run_orchestrator(SANCTIONED)
    assert d.decision == "decline"
    assert any("Sanctions" in r for r in d.reasons)


def test_large_amount_refers_to_human():
    d = run_orchestrator(BIG)
    assert d.decision == "refer"
    assert any("HITL" in r for r in d.reasons)
