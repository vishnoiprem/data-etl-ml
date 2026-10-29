"""Secure pipeline — orchestrates authz, PII, injection, generation, audit.

This is the pattern every regulated GenAI request should follow. Each step
is independent and emits an audit entry; failure at any step short-circuits
to a safe default (deny + log).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.audit import AuditLog
from src.authz import Decision, Principal, Resource, decide
from src.injection import detect as detect_injection
from src.pii import redact


@dataclass
class PipelineRequest:
    principal: Principal
    resource: Resource
    action: str                # e.g. "query"
    user_text: str             # the prompt


@dataclass
class PipelineResponse:
    allowed: bool
    answer: str | None
    blocked_at: str | None
    findings: dict = field(default_factory=dict)
    audit_seq: int | None = None


def _stub_llm_answer(sanitized_prompt: str) -> str:
    """Stand-in LLM. Returns a deterministic response.

    In production this is `bedrock-runtime.invoke_model` against Claude with
    Bedrock Guardrails attached, but the pipeline shape is the same.
    """
    return f"(Demo response acknowledging: '{sanitized_prompt[:120]}')"


def run_pipeline(req: PipelineRequest, log: AuditLog) -> PipelineResponse:
    findings: dict = {}

    # 1) Authorization
    authz: Decision = decide(req.principal, req.action, req.resource)
    log.append(
        actor=req.principal.user_id, action="authz", resource=req.resource.resource_id,
        outcome="allow" if authz.allow else "deny",
        controls=["ISO42001:A.5.15", "SOC2:CC6.1", "NIST:GOVERN-1.5"],
        payload={"action": req.action, "reasons": authz.reasons},
    )
    if not authz.allow:
        return PipelineResponse(allowed=False, answer=None, blocked_at="authz",
                                findings={"authz": authz.reasons})

    # 2) Input injection detection
    inj = detect_injection(req.user_text)
    findings["injection"] = {"risk": inj.risk_score, "reasons": inj.reasons}
    log.append(
        actor=req.principal.user_id, action="injection_check",
        resource=req.resource.resource_id,
        outcome="deny" if inj.blocked else "allow",
        controls=["ISO42001:A.6.2.5", "NIST:MEASURE-2.6"],
        payload={"risk": inj.risk_score, "reasons": inj.reasons},
    )
    if inj.blocked:
        return PipelineResponse(allowed=False, answer=None, blocked_at="injection",
                                findings=findings)

    # 3) Input PII redaction
    inp_red = redact(req.user_text)
    findings["input_pii"] = inp_red.findings
    log.append(
        actor=req.principal.user_id, action="input_redact",
        resource=req.resource.resource_id, outcome="ok",
        controls=["ISO42001:A.7.4", "SOC2:P5.1", "NIST:MAP-4.1"],
        payload={"redactions": [f["rule"] for f in inp_red.findings]},
    )

    # 4) Model generation (stub)
    raw = _stub_llm_answer(inp_red.text)

    # 5) Output PII redaction (belt + braces)
    out_red = redact(raw)
    findings["output_pii"] = out_red.findings
    log.append(
        actor=req.principal.user_id, action="generate",
        resource=req.resource.resource_id, outcome="ok",
        controls=["ISO42001:A.7.4", "NIST:MEASURE-2.10"],
        payload={"output_redactions": [f["rule"] for f in out_red.findings]},
    )

    # 6) Final entry
    final = log.append(
        actor=req.principal.user_id, action="response",
        resource=req.resource.resource_id, outcome="ok",
        controls=["SOC2:CC4.1", "ISO42001:A.5.32"],
        payload={"answer_preview": out_red.text[:80]},
    )

    return PipelineResponse(
        allowed=True, answer=out_red.text, blocked_at=None,
        findings=findings, audit_seq=final.seq,
    )
