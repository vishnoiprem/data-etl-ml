"""OpenAI / Anthropic-style multi-tenant inference platform: rate limits + cost.

If you're serving more than one team, cost attribution isn't optional.
This toy captures: a tenant registry, per-tenant rate limits, per-tenant
cost accumulation, and a token-budget guard.

Same ideas the public APIs run on, just with a few eyes on the dashboard.
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tenant:
    tenant_id: str
    rate_limit_rpm: int = 60              # requests per minute
    daily_token_budget: int = 1_000_000
    spent_tokens_today: int = 0
    allowed: bool = True


@dataclass
class InferenceRequest:
    tenant_id: str
    prompt_tokens: int
    expected_output_tokens: int
    model: str = "default"


@dataclass
class Decision:
    allowed: bool
    reason: str = ""
    tenant_id: str = ""


class MultiTenantGateway:
    def __init__(self):
        self.tenants: dict[str, Tenant] = {}
        self._window: dict[str, deque[float]] = {}  # tenant -> timestamps in last 60s

    def register(self, tenant: Tenant) -> None:
        self.tenants[tenant.tenant_id] = tenant
        self._window[tenant.tenant_id] = deque()

    def _prune_window(self, tenant_id: str, now: float) -> None:
        dq = self._window[tenant_id]
        while dq and now - dq[0] > 60:
            dq.popleft()

    def allow(self, req: InferenceRequest, now: Optional[float] = None) -> Decision:
        t = self.tenants.get(req.tenant_id)
        if t is None:
            return Decision(allowed=False, reason="unknown tenant", tenant_id=req.tenant_id)
        if not t.allowed:
            return Decision(allowed=False, reason="tenant disabled", tenant_id=req.tenant_id)
        now = now if now is not None else time.time()
        self._prune_window(req.tenant_id, now)
        dq = self._window[req.tenant_id]
        if len(dq) >= t.rate_limit_rpm:
            return Decision(allowed=False, reason="rate limit exceeded", tenant_id=req.tenant_id)
        needed = req.prompt_tokens + req.expected_output_tokens
        if t.spent_tokens_today + needed > t.daily_token_budget:
            return Decision(allowed=False, reason="daily budget exceeded", tenant_id=req.tenant_id)
        dq.append(now)
        t.spent_tokens_today += needed
        return Decision(allowed=True, tenant_id=req.tenant_id)

    def reset_daily(self) -> None:
        for t in self.tenants.values():
            t.spent_tokens_today = 0

    def report(self) -> dict:
        return {
            t.tenant_id: {
                "rpm_used": len(self._window[t.tenant_id]),
                "rpm_limit": t.rate_limit_rpm,
                "tokens_used_today": t.spent_tokens_today,
                "daily_budget": t.daily_token_budget,
            }
            for t in self.tenants.values()
        }


if __name__ == "__main__":
    gw = MultiTenantGateway()
    gw.register(Tenant(tenant_id="team-a", rate_limit_rpm=3, daily_token_budget=10_000))
    gw.register(Tenant(tenant_id="team-b", rate_limit_rpm=10, daily_token_budget=10_000))

    # Team A burns through their rate limit
    for i in range(5):
        d = gw.allow(InferenceRequest(tenant_id="team-a", prompt_tokens=100, expected_output_tokens=200))
        print(f"team-a req {i}: allowed={d.allowed} ({d.reason})")
    # Team B comes in fresh
    for i in range(2):
        d = gw.allow(InferenceRequest(tenant_id="team-b", prompt_tokens=100, expected_output_tokens=200))
        print(f"team-b req {i}: allowed={d.allowed} ({d.reason})")
    # Team A over-spends
    d = gw.allow(InferenceRequest(tenant_id="team-a", prompt_tokens=9000, expected_output_tokens=2000))
    print(f"team-a over-spend: allowed={d.allowed} ({d.reason})")
    print(f"\nreport: {gw.report()}")
