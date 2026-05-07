"""Hierarchical orchestrator.

Routes the application through KYC → Credit → Policy specialists, then
makes the final decision (approve / decline / refer-to-human).

Routing rules:
  - Hard reject if KYC fails (sanctions hit, PEP, ID fail)
  - Refer to human if amount > $250K (HITL gate)
  - Approve only if all gates pass
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from loguru import logger

from src.agent import AgentResult, CreditAgent, KYCAgent, PolicyAgent
from src.memory import Step


HITL_THRESHOLD = 250_000


@dataclass
class Decision:
    app_id: str
    decision: str            # "approve" | "decline" | "refer"
    reasons: list[str] = field(default_factory=list)
    kyc: dict | None = None
    credit: dict | None = None
    policy: dict | None = None
    trace: list[dict] = field(default_factory=list)
    cost_steps: int = 0


def _trace(result: AgentResult) -> list[dict]:
    return [
        {"agent": result.agent, "thought": s.thought, "action": s.action,
         "args": s.args, "obs": s.observation, "ok": s.ok}
        for s in result.steps
    ]


def run_orchestrator(application: dict) -> Decision:
    """Run the hierarchical multi-agent flow."""
    state: dict[str, Any] = dict(application)
    state["tool_outputs"] = {}
    decision = Decision(app_id=application["app_id"], decision="pending")
    trace: list[dict] = []

    # 1) KYC
    kyc_state = dict(state)
    kyc_state["tool_outputs"] = {}
    kyc_result = KYCAgent().run(kyc_state)
    decision.kyc = kyc_result.output
    trace.extend(_trace(kyc_result))
    if not kyc_result.success or kyc_result.output.get("sanctions_hit") or \
       not kyc_result.output.get("id_verified"):
        decision.decision = "decline"
        decision.reasons.append("KYC failed")
        if kyc_result.output.get("sanctions_hit"):
            decision.reasons.append("Sanctions list hit")
        if not kyc_result.output.get("id_verified"):
            decision.reasons.append("Identity not verified")
        decision.trace = trace
        decision.cost_steps = len(trace)
        return decision

    # 2) Credit
    credit_state = dict(state)
    credit_state["tool_outputs"] = {}
    credit_result = CreditAgent().run(credit_state)
    decision.credit = credit_result.output
    trace.extend(_trace(credit_result))
    if not credit_result.success:
        decision.decision = "refer"
        decision.reasons.append(f"Credit step failed: {credit_result.failure_reason}")
        decision.trace = trace
        decision.cost_steps = len(trace)
        return decision

    # 3) Policy (uses credit + dti from prior step)
    policy_state = dict(state)
    policy_state["tool_outputs"] = {}
    policy_state["dti"] = credit_result.output.get("dti", 1.0)
    policy_state["credit_score"] = credit_result.output.get("credit_score", 0)
    policy_result = PolicyAgent().run(policy_state)
    decision.policy = policy_result.output
    trace.extend(_trace(policy_result))

    # 4) Final routing
    decision.cost_steps = len(trace)
    decision.trace = trace

    # HITL gate for large dollar amounts
    if state["amount"] > HITL_THRESHOLD:
        decision.decision = "refer"
        decision.reasons.append(f"Amount ${state['amount']:,} > HITL threshold ${HITL_THRESHOLD:,}")
        return decision

    if not policy_result.output.get("policy_pass"):
        decision.decision = "decline"
        decision.reasons.extend(policy_result.output.get("policy_reasons", []))
        return decision

    if credit_result.output.get("delinquencies_24m", 0) >= 1:
        decision.decision = "refer"
        decision.reasons.append("Delinquency in last 24 months")
        return decision

    decision.decision = "approve"
    decision.reasons.append("All gates passed")
    return decision
