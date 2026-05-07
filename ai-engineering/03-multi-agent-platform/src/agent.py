"""ReAct-style single agent.

In production this loop is driven by an LLM choosing tools via
Bedrock's `tool_use` blocks. For the offline demo, each specialist runs a
deterministic policy that produces the same call sequence a well-prompted
LLM would.

The point isn't the LLM — it's the **loop structure**:
  - bounded steps (budget guard)
  - loop detection (signature of last N steps)
  - structured tool calls (no free-text execution)
  - explicit termination with a result
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from loguru import logger

from src.memory import ShortTermMemory, Step
from src.tools import TOOLS, ToolResult


@dataclass
class AgentResult:
    agent: str
    success: bool
    output: dict
    steps: list[Step] = field(default_factory=list)
    failure_reason: str | None = None


class Agent(ABC):
    """Specialist agent base class.

    Concrete agents implement `policy(state, memory)` to decide the next
    action. This mirrors what a tool-using LLM does: examine the state +
    history and emit (thought, action, args).
    """

    name: str = "agent"
    max_steps: int = 10

    def __init__(self):
        self.memory = ShortTermMemory(max_steps=self.max_steps)

    @abstractmethod
    def policy(self, state: dict) -> tuple[str, str, dict] | None:
        """Return (thought, tool_name, args) or None to terminate."""

    @abstractmethod
    def aggregate(self, state: dict) -> dict:
        """Build the final output once the agent terminates."""

    def step(self, state: dict) -> Step | None:
        decision = self.policy(state)
        if decision is None:
            return None
        thought, tool_name, args = decision
        if tool_name not in TOOLS:
            logger.warning(f"[{self.name}] hallucinated tool {tool_name}")
            return Step(thought=thought, action=tool_name, args=args, observation={}, ok=False)
        result: ToolResult = TOOLS[tool_name](**args)
        # Update mutable state with tool output
        state.setdefault("tool_outputs", {})[tool_name] = result.data
        return Step(thought=thought, action=tool_name, args=args, observation=result.data, ok=result.ok)

    def run(self, state: dict) -> AgentResult:
        for i in range(self.max_steps):
            step = self.step(state)
            if step is None:
                # Agent decided to terminate
                return AgentResult(agent=self.name, success=True, output=self.aggregate(state),
                                    steps=list(self.memory.steps))
            self.memory.add(step)
            if not step.ok:
                return AgentResult(
                    agent=self.name, success=False, output=self.aggregate(state),
                    steps=list(self.memory.steps),
                    failure_reason=f"tool {step.action} failed: {step.observation}",
                )
            # Loop guard
            if i >= 3:
                sig = self.memory.loop_signature(3)
                last_3 = " | ".join(f"{s.action}({sorted(s.args.items())})"
                                    for s in list(self.memory.steps)[-3:])
                if sig == last_3 and i > 5:
                    return AgentResult(
                        agent=self.name, success=False, output={},
                        steps=list(self.memory.steps),
                        failure_reason="loop detected",
                    )
        return AgentResult(
            agent=self.name, success=False, output=self.aggregate(state),
            steps=list(self.memory.steps),
            failure_reason="step budget exhausted",
        )


# ----------------------------- KYC Agent -----------------------------------

class KYCAgent(Agent):
    name = "kyc"

    def policy(self, state):
        outputs = state.get("tool_outputs", {})
        if "id_verify" not in outputs:
            return ("Verify identity first.", "id_verify",
                    {"name": state["name"], "dob": state["dob"], "ssn_last4": state["ssn_last4"]})
        if "sanctions_check" not in outputs:
            return ("Run sanctions check.", "sanctions_check",
                    {"name": state["name"], "country": state["country"]})
        if "pep_check" not in outputs:
            return ("Check PEP status.", "pep_check", {"name": state["name"]})
        return None  # terminate

    def aggregate(self, state):
        out = state.get("tool_outputs", {})
        return {
            "id_verified": out.get("id_verify", {}).get("id_verified", False),
            "sanctions_hit": out.get("sanctions_check", {}).get("hit", False),
            "is_pep": out.get("pep_check", {}).get("is_pep", False),
        }


# ----------------------------- Credit Agent --------------------------------

class CreditAgent(Agent):
    name = "credit"

    def policy(self, state):
        outputs = state.get("tool_outputs", {})
        if "bureau_pull" not in outputs:
            return ("Pull credit bureau report.", "bureau_pull",
                    {"ssn_last4": state["ssn_last4"]})
        if "income_verify" not in outputs:
            return ("Verify income.", "income_verify",
                    {"name": state["name"], "income_annual": state["income_annual"]})
        if "dti_calculate" not in outputs:
            # Crude monthly-payment estimate: 5-year amortizing at 8% APR
            r = 0.08 / 12
            n = 60
            p = state["amount"]
            monthly = p * r * (1 + r) ** n / ((1 + r) ** n - 1)
            return ("Compute DTI for proposed loan.", "dti_calculate", {
                "income_annual": state["income_annual"],
                "monthly_debt": state["monthly_debt"],
                "new_loan_monthly": round(monthly, 2),
            })
        return None

    def aggregate(self, state):
        out = state.get("tool_outputs", {})
        return {
            "credit_score": out.get("bureau_pull", {}).get("credit_score"),
            "delinquencies_24m": out.get("bureau_pull", {}).get("delinquencies_24m", 0),
            "income_verified": out.get("income_verify", {}).get("verified", False),
            "dti": out.get("dti_calculate", {}).get("dti"),
        }


# ----------------------------- Policy Agent --------------------------------

class PolicyAgent(Agent):
    name = "policy"

    def policy(self, state):
        outputs = state.get("tool_outputs", {})
        if "jurisdiction_rules" not in outputs:
            return ("Look up rules for state + purpose.", "jurisdiction_rules",
                    {"state": state["state"], "purpose": state["purpose"]})
        if "rule_engine" not in outputs:
            rules = outputs["jurisdiction_rules"]
            return ("Evaluate against rule engine.", "rule_engine", {
                "amount": state["amount"],
                "dti": state.get("dti", 0.99),
                "credit_score": state.get("credit_score", 0),
                "rules": rules,
            })
        return None

    def aggregate(self, state):
        out = state.get("tool_outputs", {})
        re = out.get("rule_engine", {})
        return {"policy_pass": re.get("pass", False), "policy_reasons": re.get("reasons", [])}
