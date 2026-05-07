"""Attribute-based access control (ABAC) policy engine.

Production maps to AWS IAM Identity Center + ABAC tag conditions, or
Cedar policies via Verified Permissions. The mental model is the same:

  decide(principal, action, resource, context) → allow | deny

Policies are deny-by-default; an explicit DENY always wins.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Principal:
    user_id: str
    tenant_id: str
    roles: list[str]                  # e.g. ["analyst"]
    clearance: str = "tier1"          # tier1..tier4


@dataclass
class Resource:
    resource_id: str
    tenant_id: str
    classification: str               # "public" | "internal" | "confidential" | "restricted"
    required_clearance: str = "tier1"


@dataclass
class Decision:
    allow: bool
    reasons: list[str] = field(default_factory=list)


CLEARANCE_RANK = {"tier1": 1, "tier2": 2, "tier3": 3, "tier4": 4}


def decide(principal: Principal, action: str, resource: Resource, context: dict | None = None) -> Decision:
    reasons: list[str] = []

    # Tenant isolation: hard rule
    if principal.tenant_id != resource.tenant_id:
        return Decision(allow=False, reasons=["cross-tenant access blocked"])

    # Clearance check
    if CLEARANCE_RANK.get(principal.clearance, 0) < CLEARANCE_RANK.get(resource.required_clearance, 99):
        return Decision(allow=False, reasons=[
            f"insufficient clearance ({principal.clearance} < {resource.required_clearance})"
        ])

    # Action-role check
    role_actions = {
        "analyst": {"read", "query"},
        "data_scientist": {"read", "query", "embed"},
        "admin": {"read", "query", "embed", "write", "delete"},
        "auditor": {"read", "query", "audit_read"},
    }
    allowed = set()
    for role in principal.roles:
        allowed |= role_actions.get(role, set())
    if action not in allowed:
        return Decision(allow=False, reasons=[
            f"action '{action}' not permitted for roles {principal.roles}"
        ])

    reasons.append(f"action '{action}' permitted for roles {principal.roles}")
    reasons.append(f"clearance {principal.clearance} >= {resource.required_clearance}")
    return Decision(allow=True, reasons=reasons)
