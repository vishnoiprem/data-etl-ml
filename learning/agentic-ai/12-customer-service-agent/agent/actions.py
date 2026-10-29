"""
Action graph for a customer-service agent.

Every action declares: is it reversible? Does it need consent? Does it
need a human? Is there a dollar cap?

This is the layer that turns "LLM with tools" into a system that can
actually touch real money. Without it, the agent will eventually do
something irreversible without asking.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class ActionClass(str, Enum):
    READ = "read"               # safe
    REVERSIBLE = "reversible"   # undoable
    NEEDS_CONSENT = "consent"   # ask customer
    NEEDS_HUMAN = "human"       # human-in-loop


@dataclass
class Action:
    name: str
    cls: ActionClass
    max_amount_cents: int = 0
    description: str = ""


# The reference action set. Real impl: loaded from a config.
ACTIONS = {
    "read_ticket":       Action("read_ticket",       ActionClass.READ,           description="view a ticket"),
    "search_kb":         Action("search_kb",         ActionClass.READ,           description="search the knowledge base"),
    "resend_receipt":    Action("resend_receipt",    ActionClass.REVERSIBLE,     description="resend a receipt email"),
    "refund_small":      Action("refund_small",      ActionClass.NEEDS_CONSENT, max_amount_cents=5000,
                                description="refund up to $50 (asks customer first)"),
    "refund_large":      Action("refund_large",      ActionClass.NEEDS_HUMAN,   max_amount_cents=0,
                                description="refund over $50 (human approves)"),
    "cancel_sub":        Action("cancel_sub",        ActionClass.NEEDS_CONSENT, description="cancel a subscription (asks)"),
    "wire_transfer":     Action("wire_transfer",     ActionClass.NEEDS_HUMAN,   description="initiate a wire transfer (human only)"),
}


def can_agent_run(action: str, amount_cents: int = 0, has_consent: bool = False) -> tuple[bool, str]:
    """Returns (allowed, reason)."""
    a = ACTIONS.get(action)
    if not a:
        return False, f"unknown action: {action}"
    if a.cls == ActionClass.READ:
        return True, "read is always allowed"
    if a.cls == ActionClass.REVERSIBLE:
        return True, "reversible action is allowed without consent"
    if a.cls == ActionClass.NEEDS_CONSENT:
        if not has_consent:
            return False, "needs customer consent"
        if amount_cents > a.max_amount_cents:
            return False, f"over consent cap (${a.max_amount_cents/100:.2f})"
        return True, "consent + within cap"
    if a.cls == ActionClass.NEEDS_HUMAN:
        return False, "requires human approval"
    return False, "no class"


if __name__ == "__main__":
    for desc, action, amount, consent in [
        ("read a ticket",          "read_ticket",  0,    False),
        ("resend receipt",         "resend_receipt", 0,  False),
        ("refund $20 with consent","refund_small",  2000, True),
        ("refund $20 no consent",  "refund_small",  2000, False),
        ("refund $200 small",      "refund_small",  20000, True),  # over cap
        ("refund $200 large",      "refund_large",  20000, True),  # human
        ("wire $1000",             "wire_transfer", 100000, True),# human
    ]:
        ok, reason = can_agent_run(action, amount, consent)
        print(f"{desc!r}: allowed={ok}  {reason}")
