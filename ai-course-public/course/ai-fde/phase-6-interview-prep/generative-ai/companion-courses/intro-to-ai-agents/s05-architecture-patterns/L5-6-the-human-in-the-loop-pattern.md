# L5.6: The human-in-the-loop pattern

> **FDE framing in one line:** the human-in-the-loop pattern is the safety net for irreversible side effects. The agent pauses for approval before sending an email, moving money, or deleting data. The right pattern when the cost of a wrong action exceeds the cost of a human review.

## The 3 things you'll learn

1. The 3 levels of human-in-the-loop: approval before action (pre-execution), approval after action (post-execution review), approval on demand (the human can interrupt).
2. The 4-axis HITL rubric: action reversibility, action cost, action frequency, customer trust level.
3. The "approval threshold" pattern: the agent auto-approves actions below the threshold; the human approves above it. The default threshold is $100 for refunds, $0 for sends.

## Concept

The human-in-the-loop (HITL) pattern is the safety net for irreversible side effects. Some agent actions have consequences the FDE cannot undo with code: sending an email to a customer, moving money between accounts, deleting a user record. For these actions, the agent must pause and request human approval before executing. **The HITL pattern is the difference between an agent that is safe to deploy and one that is a liability.**

The 3 levels of human-in-the-loop:

1. **Approval before action (pre-execution).** The agent pauses before executing the action; the human reviews the action and approves/rejects. Use for high-stakes actions (move money > $100, delete user, send email to > 100 recipients). The agent cannot proceed without approval; the human is in the critical path.
2. **Approval after action (post-execution review).** The agent executes the action; the human reviews the action afterward and can roll back. Use for medium-stakes actions (refund < $100, send email to 1 recipient, update user record). The agent proceeds; the human is in the audit path.
3. **Approval on demand (interrupt).** The agent executes the action; the human can interrupt at any time. Use for low-stakes actions (read-only queries, internal tool calls). The human is not in the path; the human can intervene if they notice something wrong.

The 4-axis HITL rubric:

1. **Action reversibility.** Can the action be undone? Yes (read, write-with-idempotency) → post-execution review. No (send, move, delete) → pre-execution approval.
2. **Action cost.** What is the cost of a wrong action? Low (< $10) → on demand. Medium ($10-$100) → post-execution review. High (> $100) → pre-execution approval.
3. **Action frequency.** How often does the action happen? Rare (1/day) → pre-execution approval. Common (10-100/day) → post-execution review. Frequent (> 100/day) → on demand (humans can't review 1000 actions/day).
4. **Customer trust level.** How much does the customer trust the agent? Low (early deployment) → pre-execution approval. Medium (proven track record) → post-execution review. High (mature deployment) → on demand.

The "approval threshold" pattern is the FDE's primary design heuristic. The agent auto-approves actions below the threshold; the human approves above it. The default threshold is $100 for refunds, $0 for sends (every send is reviewed), 1000 recipients for broadcasts. The threshold is a config value in the system prompt; the dispatcher enforces it.

## The pattern

The HITL pattern, as a decorator on tool calls:

```python
class ApprovalRequired(Exception):
    """Raised when a tool call requires human approval."""
    def __init__(self, tool_name: str, args: dict, reason: str):
        self.tool_name = tool_name
        self.args = args
        self.reason = reason

def require_approval_above(threshold_usd: float, tool_name: str):
    """Decorator: require human approval for tool calls above the threshold."""
    def decorator(func):
        def wrapper(args: dict, state: dict) -> dict:
            amount = args.get("amount_usd", 0) or args.get("total_usd", 0)
            if amount > threshold_usd:
                # Check if the human has already approved
                if not state.get("approvals", {}).get(f"{tool_name}:{json.dumps(args, sort_keys=True)}"):
                    raise ApprovalRequired(tool_name, args, f"amount ${amount} > threshold ${threshold_usd}")
            return func(args)
        return wrapper
    return decorator

# Example: refund.create requires approval above $100
@require_approval_above(threshold_usd=100.0, tool_name="refund.create")
def refund_create(args):
    return refund_api.create(**args)
```

The LangGraph interrupt pattern (the production-grade HITL):

```python
from langgraph.graph import StateGraph, interrupt

def approval_node(state: dict) -> dict:
    """The agent pauses here for human approval."""
    approval = interrupt({
        "question": f"Approve {state['pending_action']}?",
        "action": state["pending_action"],
        "args": state["pending_args"],
        "amount_usd": state["pending_args"].get("amount_usd", 0),
    })
    if approval.get("approved"):
        return {"approved": True}
    return {"approved": False, "reason": approval.get("reason", "rejected")}

# Wire the approval node into the graph
graph = StateGraph(SupportState)
graph.add_node("check_amount", check_amount_node)
graph.add_node("approval", approval_node)  # Pauses here
graph.add_node("execute_refund", execute_refund_node)
graph.add_conditional_edges("check_amount",
    lambda s: "approval" if s.refund_amount_usd > 100 else "execute_refund",
    {"approval": "approval", "execute_refund": "execute_refund"})
graph.add_edge("approval", "execute_refund",
    lambda s: "execute_refund" if s.approved else "end")
```

The approval state management:

```python
class ApprovalStore:
    """Persistent store for human approvals. The audit trail."""

    def __init__(self):
        self.approvals = {}  # key: tool_name + args_hash -> {approved, approver, timestamp}

    def request_approval(self, tool_name: str, args: dict) -> str:
        """Request approval; returns the request_id."""
        request_id = f"req-{uuid.uuid4()}"
        self.approvals[request_id] = {
            "tool": tool_name, "args": args, "status": "pending",
            "requested_at": datetime.now().isoformat(),
        }
        return request_id

    def approve(self, request_id: str, approver: str) -> bool:
        self.approvals[request_id].update({
            "status": "approved", "approver": approver,
            "approved_at": datetime.now().isoformat(),
        })
        return True

    def reject(self, request_id: str, approver: str, reason: str) -> bool:
        self.approvals[request_id].update({
            "status": "rejected", "approver": approver, "reason": reason,
            "rejected_at": datetime.now().isoformat(),
        })
        return False
```

The pattern that wins interviews is the "3 levels + approval threshold + interrupt" pattern. The candidate who says "HITL is the safety net for irreversible side effects. 3 levels: pre-execution approval (move money > $100, delete user), post-execution review (refund < $100, send email), on demand (read-only). The approval threshold is configurable: $100 for refunds, $0 for sends, 1000 for broadcasts. The interrupt pattern lets the human intervene at any time. The wrong choice is pre-execution approval for every action (humans become the bottleneck). The wrong choice is no approval for high-stakes actions (the agent sends a $10K refund by mistake). The right choice is the threshold + the audit log + the interrupt" is the candidate who demonstrates the HITL-mindset.

## Code or example

The HITL rubric in action:

```python
def pick_hitl_level(tool_name: str, args: dict, customer_trust: str = "medium") -> str:
    """Pick pre-execution, post-execution, or on-demand based on the action."""
    # Reversibility
    irreversible_tools = {"send_email", "move_money", "delete_user", "broadcast"}
    if tool_name in irreversible_tools:
        return "pre_execution" if customer_trust != "high" else "post_execution"

    # Cost
    amount = args.get("amount_usd", 0)
    if amount > 100:
        return "pre_execution"
    if amount > 10:
        return "post_execution"

    # Frequency (estimated)
    if args.get("recipient_count", 1) > 100:
        return "pre_execution"

    return "on_demand"
```

The PacificFreight approval thresholds (the canonical FDE use case):

```python
APPROVAL_THRESHOLDS = {
    "refund.create": {"pre_execution_above_usd": 100, "post_execution_above_usd": 10},
    "send_email": {"pre_execution_always": True},  # Every send is reviewed
    "escalate.to_human": {"pre_execution_always": False},  # Auto-approve escalations
    "translate.to": {"pre_execution_always": False},  # Auto-approve translations
    "tracker.lookup": {"pre_execution_always": False},  # Read-only, no approval
    "delete_shipment": {"pre_execution_always": True},  # Always require approval
}

# Mei (CS) can approve refunds up to $100; her manager approves $100-$1000;
# the CFO approves > $1000. The threshold is per-role, not per-agent.
```

The audit log for HITL (the artifact the on-call reads):

```python
HITL_AUDIT_LOG_ENTRY = {
    "timestamp": "2026-10-10T14:23:45Z",
    "request_id": "req-abc123",
    "tool": "refund.create",
    "args": {"shipment_id": "PF-1003", "amount_usd": 50, "idempotency_key": "PF-1003-50-2026-10-10"},
    "amount_usd": 50,
    "threshold": 100,
    "hitl_level": "post_execution",  # Below threshold, no pre-approval needed
    "status": "approved_post_execution",  # Reviewed and approved after execution
    "approver": "mei@pf.com",
    "review_notes": "Customer requested refund for damaged package; within policy.",
}
```

## Production addendum

The HITL question is the answer to "how do you put a human in the agent's loop." The 60-second script:

> "Three levels. Pre-execution approval (pause before action): for high-stakes, irreversible, high-cost actions (move money > $100, delete user, send to > 100 recipients). Post-execution review (action proceeds, human reviews after): for medium-stakes actions (refund < $100, send email to 1 recipient). On demand (human can interrupt): for low-stakes, read-only actions. **The approval threshold is configurable: $100 for refunds, $0 for sends, 1000 for broadcasts.** The interrupt pattern lets the human intervene at any time. The audit log records every approval decision. The wrong choice is pre-execution approval for every action (humans become the bottleneck, agent is unusable). The wrong choice is no approval for high-stakes actions (the agent sends a $10K refund by mistake). The right choice is the threshold + the 3 levels + the audit log."

This is the difference between a candidate who says "we have human review" and a candidate who says "3 levels (pre-execution, post-execution, on-demand), configurable threshold ($100 for refunds), interrupt pattern, audit log." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-4-langgraph.py` — the LangGraph interrupt pattern with HUMAN_APPROVAL_THRESHOLD_USD=100.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/16-hitl-agent.py` — the production HITL with approval store + audit log.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/09-human-in-the-loop.md` — the HITL as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/` — the MCP tool policy file as the approval configuration.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — HITL as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you put a human in the agent's loop?"** Answer: 3 levels — pre-execution approval (pause before action for high-stakes), post-execution review (action proceeds, human reviews after for medium-stakes), on demand (human can interrupt for low-stakes). The approval threshold is configurable ($100 for refunds). The interrupt pattern lets the human intervene at any time. The audit log records every approval decision.
2. **"What is the approval threshold pattern?"** Answer: the agent auto-approves actions below the threshold; the human approves above it. Default thresholds: $100 for refunds, $0 for sends, 1000 for broadcasts. The threshold is a config value in the system prompt; the dispatcher enforces it. The threshold can be per-role (Mei approves up to $100, her manager approves $100-$1000, the CFO approves > $1000).
3. **"What is the difference between pre-execution, post-execution, and on-demand HITL?"** Answer: pre-execution is pause-before-action (high-stakes: move money > $100); post-execution is proceed-then-review (medium-stakes: refund < $100); on-demand is human-can-interrupt (low-stakes: read-only). The choice depends on action reversibility, cost, frequency, and customer trust level. **Pre-execution is the safest; on-demand is the fastest; post-execution is the middle ground.**

## Read next

`S6-implementing-agents/L6-1-the-agent-framework-ecosystem.md` — Section 6 dives into the implementation: which framework to pick (LangChain, LangGraph, LlamaIndex, AutoGen, CrewAI), how to evaluate them, and how to ship a production agent on a budget.