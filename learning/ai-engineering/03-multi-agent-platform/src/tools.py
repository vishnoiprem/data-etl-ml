"""Stub tool implementations.

These mirror the JSON-schema tool definitions you'd register with a Bedrock
Agent or an MCP server. They're deterministic stubs so the demo runs without
external services. In production, each is a Lambda action group or an MCP
server endpoint.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class ToolResult:
    ok: bool
    data: dict
    error: str | None = None


# --- KYC tools --------------------------------------------------------------

def id_verify(name: str, dob: str, ssn_last4: str) -> ToolResult:
    """Stub: passes if SSN last4 is digits and DOB looks valid."""
    if len(ssn_last4) == 4 and ssn_last4.isdigit() and len(dob) == 10:
        return ToolResult(ok=True, data={"id_verified": True, "match_score": 0.97})
    return ToolResult(ok=False, data={"id_verified": False}, error="ID verification failed")


def sanctions_check(name: str, country: str) -> ToolResult:
    """Stub OFAC/sanctions check. Deterministic: certain names trigger hits."""
    blocklist = {"evan petrov"}  # demo-only
    if name.lower() in blocklist:
        return ToolResult(ok=True, data={"hit": True, "list": "OFAC SDN", "confidence": 0.92})
    return ToolResult(ok=True, data={"hit": False})


def pep_check(name: str) -> ToolResult:
    """Stub Politically Exposed Person check."""
    return ToolResult(ok=True, data={"is_pep": False})


# --- Credit tools -----------------------------------------------------------

def bureau_pull(ssn_last4: str) -> ToolResult:
    """Stub credit-bureau pull. Returns a deterministic score from the SSN last4."""
    h = int(hashlib.md5(ssn_last4.encode()).hexdigest(), 16)
    score = 580 + (h % 240)  # 580..819
    return ToolResult(ok=True, data={
        "credit_score": score,
        "open_accounts": 3 + (h % 6),
        "delinquencies_24m": (h % 7) // 5,  # 0 or 1
    })


def income_verify(name: str, income_annual: float) -> ToolResult:
    """Stub income verification."""
    # In a real flow this would call payroll providers.
    return ToolResult(ok=True, data={"verified": True, "stated_vs_verified": 1.0})


def dti_calculate(income_annual: float, monthly_debt: float, new_loan_monthly: float) -> ToolResult:
    """Debt-to-Income ratio calculation."""
    monthly_income = income_annual / 12.0
    if monthly_income <= 0:
        return ToolResult(ok=False, data={}, error="Invalid income")
    dti = (monthly_debt + new_loan_monthly) / monthly_income
    return ToolResult(ok=True, data={"dti": round(dti, 3), "monthly_income": round(monthly_income, 2)})


# --- Policy tools -----------------------------------------------------------

def jurisdiction_rules(state: str, purpose: str) -> ToolResult:
    """State + product policy lookup."""
    rules = {
        ("CA", "auto"): {"max_amount": 100000, "max_dti": 0.45, "min_score": 650},
        ("TX", "home_purchase"): {"max_amount": 1000000, "max_dti": 0.43, "min_score": 700},
        ("NY", "small_business"): {"max_amount": 250000, "max_dti": 0.50, "min_score": 680},
        ("WA", "personal"): {"max_amount": 50000, "max_dti": 0.40, "min_score": 660},
        ("FL", "investment_property"): {"max_amount": 1500000, "max_dti": 0.45, "min_score": 720},
    }
    r = rules.get((state, purpose))
    if not r:
        return ToolResult(ok=False, data={}, error=f"No rules for ({state}, {purpose})")
    return ToolResult(ok=True, data=r)


def rule_engine(amount: float, dti: float, credit_score: int, rules: dict) -> ToolResult:
    """Evaluate the application against jurisdiction rules."""
    reasons = []
    if amount > rules.get("max_amount", float("inf")):
        reasons.append(f"amount {amount} > max {rules['max_amount']}")
    if dti > rules.get("max_dti", 1.0):
        reasons.append(f"DTI {dti:.2f} > max {rules['max_dti']}")
    if credit_score < rules.get("min_score", 0):
        reasons.append(f"score {credit_score} < min {rules['min_score']}")
    return ToolResult(ok=True, data={"pass": not reasons, "reasons": reasons})


# --- Tool registry ----------------------------------------------------------

TOOLS = {
    "id_verify": id_verify,
    "sanctions_check": sanctions_check,
    "pep_check": pep_check,
    "bureau_pull": bureau_pull,
    "income_verify": income_verify,
    "dti_calculate": dti_calculate,
    "jurisdiction_rules": jurisdiction_rules,
    "rule_engine": rule_engine,
}


# JSON-schema-style tool definitions (the format Bedrock + Anthropic agents expect)
TOOL_SPECS = [
    {"name": "id_verify", "input_schema": {"name": "string", "dob": "string", "ssn_last4": "string"}},
    {"name": "sanctions_check", "input_schema": {"name": "string", "country": "string"}},
    {"name": "pep_check", "input_schema": {"name": "string"}},
    {"name": "bureau_pull", "input_schema": {"ssn_last4": "string"}},
    {"name": "income_verify", "input_schema": {"name": "string", "income_annual": "number"}},
    {"name": "dti_calculate", "input_schema": {"income_annual": "number", "monthly_debt": "number", "new_loan_monthly": "number"}},
    {"name": "jurisdiction_rules", "input_schema": {"state": "string", "purpose": "string"}},
    {"name": "rule_engine", "input_schema": {"amount": "number", "dti": "number", "credit_score": "number", "rules": "object"}},
]
