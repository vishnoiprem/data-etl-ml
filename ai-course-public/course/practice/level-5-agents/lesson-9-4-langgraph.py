"""
Lesson 9.4: LangGraph
====================================
LangGraph stateful workflow with branches + approval.

Run:  python lesson-9-4-langgraph.py

No external API keys required -- all LLM/DB calls are mocked.

This is a *LangGraph-equivalent* state machine. LangGraph itself is a
library; the graph structure it expresses is a directed graph with:
  - Nodes (functions that mutate state)
  - Edges (unconditional: A -> B)
  - Conditional edges (A -> B or C, based on a function of state)
  - Interrupt points (a node that pauses for human input)
  - Persistent state (a TypedDict that flows through the graph)

The lesson file is hand-rolled rather than a LangGraph import so it
runs with stdlib only. The control flow is identical to what a real
LangGraph `StateGraph` produces. See the bottom of the file for the
LangGraph equivalent of the same workflow.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "9.4"
LESSON_TITLE = "LangGraph"
DEFAULT_MODEL = "gpt-5-mini"  # 2026-current cheap+smart; mock used for the demo

# Pricing per 1M tokens, 2026-current
PRICING = {
    "gpt-5":              {"input": 2.50,  "output": 10.00},
    "gpt-5-mini":         {"input": 0.15,  "output": 0.60},
    "claude-sonnet-4.5":  {"input": 3.00,  "output": 15.00},
    "claude-haiku-4.5":   {"input": 0.80,  "output": 4.00},
    "gemini-2.5-pro":     {"input": 1.25,  "output": 5.00},
    "gemini-2.5-flash":   {"input": 0.075, "output": 0.30},
    "llama-4-70b-self":   {"input": 0.10,  "output": 0.10},
}

# Refunds over this amount require a human to approve before the
# refund is processed. Below this threshold, the agent can act alone.
HUMAN_APPROVAL_THRESHOLD_USD = 100.0

# Maximum number of node visits before we abort. Catches cycles.
MAX_NODE_VISITS = 20


# =============================================================================
# STATE -- the typed object that flows through the graph
# =============================================================================

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SupportState:
    """The state object for the customer support workflow.

    Each node reads + writes fields on this object. The graph
    orchestrator passes the same instance to every node.
    """
    request_id: str
    user_message: str
    # Populated by `classify`
    intent: Optional[str] = None            # "refund" | "complaint" | "question"
    confidence: float = 0.0
    # Populated by `ask_order_id` (refund path)
    order_id: Optional[str] = None
    refund_amount_usd: float = 0.0
    # Populated by `answer_with_rag` (question path)
    answer: Optional[str] = None
    # Populated by `human_approval` (refund > threshold)
    human_approved: Optional[bool] = None
    human_approver: Optional[str] = None
    # Final status
    final_status: Optional[str] = None      # "resolved" | "escalated" | "refunded" | "answered" | "needs_input"
    # Observability: the path through the graph
    path: list[str] = field(default_factory=list)
    # Total cost accrued by the workflow (in USD, mock)
    cost_usd: float = 0.0


# =============================================================================
# MOCK LLM HELPERS -- the "node" implementations
# =============================================================================

import re

def classify_intent(user_message: str) -> tuple[str, float]:
    """Mock intent classifier. Real impl: a small LLM call with a structured prompt.

    Returns (intent, confidence). Confidence < 0.5 means we should
    escalate rather than guess.
    """
    msg = user_message.lower()
    if any(k in msg for k in ("refund", "money back", "chargeback", "i want my money")):
        return ("refund", 0.92)
    if any(k in msg for k in ("complaint", "terrible", "awful", "furious", "angry", "unacceptable", "sue")):
        return ("complaint", 0.88)
    if "?" in msg or any(k in msg for k in ("how", "what", "where", "when", "why", "do you")):
        return ("question", 0.81)
    return ("question", 0.40)  # default fallback, low confidence

def extract_order_id(user_message: str) -> Optional[str]:
    """Mock order-ID extractor. Looks for an ORD-XXXX pattern."""
    m = re.search(r"ORD-\d{4,}", user_message, re.IGNORECASE)
    return m.group(0).upper() if m else None

def lookup_order(order_id: str) -> dict:
    """Mock order lookup. Returns the order with its total."""
    return {"order_id": order_id, "total_usd": 75.00, "status": "delivered"}

def answer_with_rag(question: str) -> str:
    """Mock RAG. Returns a canned answer for a few known topics."""
    q = question.lower()
    if "shipping" in q or "delivery" in q:
        return "Standard shipping is 3-5 business days; expedited is 1-2."
    if "return" in q:
        return "Returns are accepted within 30 days of delivery for a full refund."
    if "warranty" in q:
        return "All products carry a 1-year manufacturer warranty."
    return f"[RAG] Best guess answer to: {question!r}"


# =============================================================================
# NODES -- the functions that mutate state
# =============================================================================
# In LangGraph, a node is just `(state) -> state`. Each node here
# returns the (possibly mutated) state. The orchestrator below
# dispatches to nodes by name.

def node_classify(state: SupportState) -> SupportState:
    intent, conf = classify_intent(state.user_message)
    state.intent = intent
    state.confidence = conf
    state.cost_usd += 0.0001  # mock LLM call cost
    state.path.append("classify")
    return state

def node_ask_order_id(state: SupportState) -> SupportState:
    """Refund path: ask the user for the order ID (or extract from message)."""
    oid = extract_order_id(state.user_message)
    if oid:
        state.order_id = oid
        # Only look up the amount if the caller hasn't pre-set it (e.g., the
        # demo pre-fills $250 to exercise the human-approval path).
        if state.refund_amount_usd == 0.0:
            order = lookup_order(oid)
            state.refund_amount_usd = order["total_usd"]
        state.path.append("ask_order_id:auto")
    else:
        state.final_status = "needs_input"
        state.path.append("ask_order_id:prompt")
    return state

def node_request_human_approval(state: SupportState) -> SupportState:
    """Interrupt point: pause for human approval if refund > threshold.

    In LangGraph this is `graph.interrupt(...)` or a `interrupt_before=["process_refund"]`
    on a `StateGraph`. The graph pauses; a human resumes it with a decision.
    Here we expose it as a function: the demo passes the approval in.
    """
    if state.refund_amount_usd > HUMAN_APPROVAL_THRESHOLD_USD:
        # Pause here. The human decision is supplied via approve()/reject().
        state.path.append("human_approval:pending")
        # The decision is read from state.human_approved (set by approve() before resume).
    else:
        # Below threshold: auto-approve.
        state.human_approved = True
        state.human_approver = "auto"
        state.path.append("human_approval:auto")
    return state

def node_process_refund(state: SupportState) -> SupportState:
    if not state.human_approved:
        state.final_status = "escalated"
        state.path.append("process_refund:rejected")
    else:
        state.final_status = "refunded"
        state.path.append(f"process_refund:approved_by={state.human_approver}")
    return state

def node_escalate_to_human(state: SupportState) -> SupportState:
    state.final_status = "escalated"
    state.path.append("escalate_to_human")
    return state

def node_answer_question(state: SupportState) -> SupportState:
    state.answer = answer_with_rag(state.user_message)
    state.cost_usd += 0.0002  # mock RAG cost
    state.final_status = "answered"
    state.path.append("answer_question")
    return state


# =============================================================================
# CONDITIONAL EDGES -- the routing function
# =============================================================================

def route_after_classify(state: SupportState) -> str:
    """Conditional edge: pick the next node based on the classified intent."""
    if state.confidence < 0.5:
        return "escalate_to_human"  # unsure -> escalate
    if state.intent == "refund":
        return "ask_order_id"
    if state.intent == "complaint":
        return "escalate_to_human"
    if state.intent == "question":
        return "answer_question"
    return "escalate_to_human"

def route_after_ask_order_id(state: SupportState) -> str:
    if state.final_status == "needs_input":
        return "END"  # we asked the user; wait for the next message
    return "request_human_approval"


# =============================================================================
# THE GRAPH -- a hand-rolled StateGraph
# =============================================================================

# Adjacency: node -> [(condition_fn, target_node), ...]
# The orchestrator picks the first matching edge.
EDGES = {
    "classify":              [(route_after_classify, None)],  # conditional
    "ask_order_id":          [(route_after_ask_order_id, None)],
    "request_human_approval":[(lambda s: "process_refund", None)],  # unconditional -> process_refund (which checks approval)
    "process_refund":        [],  # terminal
    "escalate_to_human":     [],  # terminal
    "answer_question":       [],  # terminal
}

# Order matters for the demo render
NODE_ORDER = ["classify", "ask_order_id", "request_human_approval",
              "process_refund", "escalate_to_human", "answer_question"]


def run_graph(state: SupportState, *, human_decision: Optional[dict] = None) -> SupportState:
    """Run the graph from the `classify` entrypoint to a terminal node.

    `human_decision` is the approval payload if the workflow paused at
    `request_human_approval` for a refund > threshold. Format:
      {"approved": bool, "approver": "alice@support.co"}
    """
    # Inject the human decision before starting
    if human_decision is not None:
        state.human_approved = human_decision.get("approved", False)
        state.human_approver = human_decision.get("approver", "unknown")
    current = "classify"
    visits: dict[str, int] = {}
    for _ in range(MAX_NODE_VISITS):
        if current == "END" or current is None:
            break
        visits[current] = visits.get(current, 0) + 1
        if visits[current] > 3:
            state.final_status = "loop_aborted"
            state.path.append("loop_abort")
            break
        # Dispatch
        node_fn = globals()[f"node_{current}"]
        state = node_fn(state)
        # Route to the next node
        edges = EDGES.get(current, [])
        if not edges:
            break  # terminal
        # First matching edge wins
        next_node = None
        for cond_fn, fixed_target in edges:
            if fixed_target:
                next_node = fixed_target
                break
            result = cond_fn(state)
            if result and result != "END":
                next_node = result
                break
        current = next_node
    return state


# =============================================================================
# DEMO -- 3 different request types
# =============================================================================

def demo():
    print("=" * 70)
    print(f"  LESSON {LESSON_NUMBER}: {LESSON_TITLE}")
    print("=" * 70)
    print()
    print("  Customer support graph: classify -> branch -> (human approval) -> END.")
    print()

    cases = [
        # Case 1: small refund (under threshold) -- auto-approved
        ("Small refund (under $100)",
         SupportState(request_id="REQ-1", user_message="I want a refund for ORD-1234."),
         None),
        # Case 2: large refund (over threshold) -- needs human approval, we approve
        ("Large refund (over $100, human-approved)",
         SupportState(request_id="REQ-2",
                      user_message="I want a refund for ORD-5678. My bill was $250.",
                      refund_amount_usd=250.00),
         {"approved": True, "approver": "alice@support.co"}),
        # Case 3: complaint -- escalate to human
        ("Complaint (escalate)",
         SupportState(request_id="REQ-3", user_message="This is unacceptable! I am furious!"),
         None),
        # Case 4: question -- answer with RAG
        ("Question (RAG answer)",
         SupportState(request_id="REQ-4", user_message="How long does shipping take?"),
         None),
    ]

    for label, state, decision in cases:
        result = run_graph(state, human_decision=decision)
        print(f"  {label}")
        print(f"    Intent:    {result.intent}  (confidence: {result.confidence:.2f})")
        print(f"    Path:      {' -> '.join(result.path)}")
        print(f"    Status:    {result.final_status}")
        if result.answer:
            print(f"    Answer:    {result.answer}")
        if result.refund_amount_usd:
            print(f"    Refund:    ${result.refund_amount_usd:.2f}  "
                  f"(threshold: ${HUMAN_APPROVAL_THRESHOLD_USD:.0f})")
        print(f"    Cost:      ${result.cost_usd:.4f}")
        print()

    # LangGraph equivalent (for reference; not executed)
    print("  LangGraph equivalent of the same workflow (sketch):")
    print("    from langgraph.graph import StateGraph, END")
    print("    g = StateGraph(SupportState)")
    print("    g.add_node('classify', node_classify)")
    print("    g.add_node('ask_order_id', node_ask_order_id)")
    print("    g.add_node('request_human_approval', node_request_human_approval)")
    print("    g.add_node('process_refund', node_process_refund)")
    print("    g.add_node('escalate_to_human', node_escalate_to_human)")
    print("    g.add_node('answer_question', node_answer_question)")
    print("    g.set_entry_point('classify')")
    print("    g.add_conditional_edges('classify', route_after_classify, {")
    print("        'ask_order_id': 'ask_order_id',")
    print("        'escalate_to_human': 'escalate_to_human',")
    print("        'answer_question': 'answer_question',})")
    print("    g.add_conditional_edges('ask_order_id', route_after_ask_order_id, {")
    print("        'request_human_approval': 'request_human_approval', END: END})")
    print("    g.add_edge('request_human_approval', 'process_refund')")
    print("    app = g.compile(interrupt_before=['process_refund'])  # human approval")
    print()

    # Cost model
    print("  LLM pricing (per 1M tokens, 2026):")
    for model, p in PRICING.items():
        print(f"    {model:<22} in=${p['input']:>6.3f}  out=${p['output']:>6.3f}")
    print()

    # Trade-offs
    print("  Design trade-offs:")
    print(f"    Human-approval threshold: ${HUMAN_APPROVAL_THRESHOLD_USD:.0f}.")
    print("    Below: agent acts alone. Above: graph pauses for a human.")
    print("    Cycles: MAX_NODE_VISITS guards against infinite loops in retry paths.")
    print("    State: a single TypedDict (or dataclass) flows through every node.")
    print("    Observability: `state.path` is the audit log of every node visit.")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demo()
