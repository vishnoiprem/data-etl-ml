"""
Mock interview simulator — Katalon Head of Data loop.

Runs the full interview day in text:
  - R1 (90 min) Vu Bui, Que Tran, Son Dao    → 4 system-design Qs
  - R2 (60 min) Duke Nguyen                   → 3 strategy Qs
  - R3 (60 min) Rajesh Krishnan               → 3 executive Qs

Each panelist asks in character. The candidate types free-text answers; the
simulator scores against criteria drawn from the scoring rubric (1–4 scale).
At the end it prints a per-panelist scorecard and overall recommendations.

Run:
  python3 mock-interview-simulator.py            # real interactive loop
  python3 mock-interview-simulator.py --demo      # prints a worked example

No external dependencies. Pure Python.
"""

from __future__ import annotations
import argparse
import json
import os
import random
import re
import textwrap
from dataclasses import dataclass, field, asdict
from typing import Callable, List, Optional


# ---------------------------------------------------------------------------
# Panelist personas — what they actually test
# ---------------------------------------------------------------------------

@dataclass
class Panelist:
    name: str
    role: str
    round_label: str
    focus: str
    style: str


PANEL = [
    Panelist("Vu Bui", "Technical Director", "R1",
             "end-to-end architecture depth, technology selection discipline",
             "calm, will follow one thread until you crack — partition sizing, cost, failure modes"),
    Panelist("Que Tran", "Solution Architect", "R1",
             "system decomposition, integration thinking, contract design",
             "tactical, asks 'what fails at 10x?' and 'how do you prevent double-counting?'"),
    Panelist("Son Dao", "Principal Software Engineer", "R1",
             "hands-on credibility, SQL, code, debugging reasoning",
             "precise, will catch hand-waving, expects code-level answers"),
    Panelist("Duke Nguyen", "VP, Engineering", "R2",
             "strategy, prioritization, Data↔Engineering interface",
             "business-first, asks 'why this and not that?', wants influence model"),
    Panelist("Rajesh Krishnan", "SVP, Engineering", "R3",
             "executive narrative, org design, investment case",
             "executive-presence, asks 'what would make this hire unquestionably successful?'"),
]


# ---------------------------------------------------------------------------
# Question bank — what each panelist is most likely to ask
# ---------------------------------------------------------------------------

@dataclass
class Question:
    qid: str
    panelist: str
    round_label: str
    prompt: str
    rubric: List[str]   # strings describing a strong answer; matched as keywords
    keywords: List[str] # phrases whose presence in the candidate's answer raises the score
    trap: str           # what a weak answer looks like


QUESTION_BANK: List[Question] = [
    # --- R1: Vu Bui (Technical Director) -----------------------------------
    Question(
        qid="Q1", panelist="Vu Bui", round_label="R1",
        prompt=("Design Katalon's global data and AI platform end-to-end. "
                "Live test execution monitoring, three-year trend analytics, "
                "flakiness detection, AI failure analysis. What are the planes, "
                "the workloads, the SLOs?"),
        keywords=["tenant_id", "event_time", "ingestion", "kafka", "lakehouse",
                  "semantic layer", "ai plane", "slo", "partition", "reconciliation",
                  "watermark", "artifact", "vector", "retrieval", "evaluation"],
        rubric=["names three planes (business / product / AI)",
                "quantifies scale with assumptions",
                "separates hot serving from durable history",
                "calls out tenant isolation as a hard floor",
                "defines data-product SLOs (not just infra SLOs)",
                "mentions evaluation BEFORE model/retrieval choice"],
        trap=("brand-first answers — 'I would use Snowflake + Databricks + Pinecone' "
              "with no sizing or trade-off"),
    ),
    Question(
        qid="Q2", panelist="Vu Bui", round_label="R1",
        prompt=("What would you NOT build in the first 90 days? What's a trap that "
                "looks like progress but isn't?"),
        keywords=["real-time olap", "data mesh", "vector database",
                  "central bi", "platform rewrite", "defer", "not build",
                  "evaluation", "ownership", "federated"],
        rubric=["names at least one non-build explicitly",
                "explains why the non-build would look productive but isn't",
                "gives a trigger condition for revisiting the decision"],
        trap="listing only safe non-builds — 'I wouldn't cut security'",
    ),

    # --- R1: Que Tran (Solution Architect) ---------------------------------
    Question(
        qid="Q5", panelist="Que Tran", round_label="R1",
        prompt=("Design ingestion for live test execution and uploaded historical "
                "reports. How do you prevent double-counting when upstream replays "
                "events?"),
        keywords=["idempotency", "event_id", "aggregate_version", "merge",
                  "partition", "tenant", "reconciliation", "manifest",
                  "schema registry", "quarantine"],
        rubric=["edge dedup by event_id",
                "sink merge keyed by business grain",
                "reconciliation against manifest counts",
                "tenant_id in partition key",
                "poison-record quarantine, not silent drop"],
        trap=("relying on 'exactly-once' messaging without idempotent sink + "
              "reconciliation"),
    ),
    Question(
        qid="Q6", panelist="Que Tran", round_label="R1",
        prompt=("A single enterprise tenant is generating 40% of peak traffic. "
                "How do you avoid noisy-neighbor impact on the other 29,999 "
                "teams?"),
        keywords=["partition", "quota", "isolation", "bucket", "burst",
                  "cost attribution", "hot tenant", "autoscaling", "rate-limit"],
        rubric=["named isolation strategy (partition / pool / quota)",
                "acknowledged burstable vs hard reject",
                "cost attribution per tenant",
                "no claim of 'just add more capacity'"],
        trap="'we'll autoscale' without naming the failure mode",
    ),

    # --- R1: Son Dao (Principal Software Engineer) -------------------------
    Question(
        qid="Q9", panelist="Son Dao", round_label="R1",
        prompt=("SQL: for each tenant/project/test/environment over the last 30 "
                "days, return run_count, first-attempt failure rate, adjacent "
                "status-transition rate, and retry recovery rate. Only groups "
                "with run_count >= 10. Walk me through the window logic."),
        keywords=["row_number", "lag", "partition by", "first_attempt",
                  "execution_id", "attempt_id", "nullif", "left join",
                  "environment_hash"],
        rubric=["uses first attempts only for transitions (no retry pollution)",
                  "handles divide-by-zero (NULLIF)",
                  "tie-breaker in order",
                  "LEFT JOIN on recovery (not inner — would drop stable tests)",
                  "mentions production caveats: shrinkage, partition pruning"],
        trap="AVG over all rows including retries — inflates transition rate",
    ),
    Question(
        qid="Q11", panelist="Son Dao", round_label="R1",
        prompt=("Kafka consumer lag is going UP and CPU is LOW. What are your "
                "top hypotheses, and what do you check first?"),
        keywords=["data skew", "hot partition", "sink backpressure", "gc",
                  "rebalance", "deserialization", "iam", "sts",
                  "rate-limit", "commit"],
        rubric=["top hypothesis is data skew, not 'need more consumers'",
                  "considers sink backpressure / GC / deserialization",
                  "names what to MEASURE (per-partition lag, GC logs)",
                  "rejects the default 'add more workers' answer"],
        trap="'we need more consumers' with no diagnosis",
    ),
    Question(
        qid="Q12", panelist="Son Dao", round_label="R1",
        prompt=("Design a safe agent that may edit a test case. What's the "
                "smallest action space, how do you prevent cross-tenant edits, "
                "and how do you make retries safe?"),
        keywords=["idempotency", "policy", "allow-list", "tenant", "audit",
                  "confirmation", "outbox", "abstain", "typed tools",
                  "read-only", "blast radius"],
        rubric=["typed tools with read-only default",
                  "policy gate runs BEFORE state",
                  "idempotency key on every mutation",
                  "explicit abstention rule",
                  "audit log captures allow + deny"],
        trap="agent with broad write access and 'prompt the user to confirm'",
    ),

    # --- R2: Duke Nguyen (VP, Engineering) ---------------------------------
    Question(
        qid="Q13", panelist="Duke Nguyen", round_label="R2",
        prompt=("Why Katalon, and why now? What's the unique data problem here?"),
        keywords=["multi-tenant", "test execution", "ai", "30k", "saas",
                  "product data", "head of data", "inflection",
                  "strategy", "platform"],
        rubric=["names something specific to Katalon (test telemetry, not generic SaaS)",
                  "connects AI roadmap to data foundation",
                  "explains why 'now' (growth, AI inflection, governance)",
                  "not brand-flattery — substance over hype"],
        trap="generic 'I love your product' without Katalon-specific signal",
    ),
    Question(
        qid="Q15", panelist="Duke Nguyen", round_label="R2",
        prompt=("Centralized, embedded, or federated data team — which and why? "
                "What breaks first in each model?"),
        keywords=["federated", "domain owner", "central platform", "paved road",
                  "ownership", "embedded", "centralized", "raci"],
        rubric=["picks federated (not the trendy answer)",
                  "explains what federated owns vs central owns",
                  "names what breaks first in each model",
                  "links to decision-quality, not team-size"],
        trap=("'centralized for control' OR 'embedded for speed' — both fail "
              "without federated ownership"),
    ),
    Question(
        qid="Q19", panelist="Duke Nguyen", round_label="R2",
        prompt=("How do you measure data-team impact without counting tickets "
                "or pipelines?"),
        keywords=["decision latency", "decision trust", "coverage",
                  "adoption", "incident rate", "slo", "certified"],
        rubric=["measures decision latency (time question → trusted answer)",
                  "measures decision trust (incidents of wrong data)",
                  "measures decision coverage (% recurring decisions with certified product)",
                  "leading indicator of adoption",
                  "NOT counting tickets or pipelines as a primary metric"],
        trap="OKR-style output metrics (X dashboards shipped)",
    ),

    # --- R3: Rajesh Krishnan (SVP, Engineering) ----------------------------
    Question(
        qid="Q20", panelist="Rajesh Krishnan", round_label="R3",
        prompt=("One-year investment case: outcomes, headcount, platform spend, "
                "risks. What would you NOT invest in?"),
        keywords=["outcome", "headcount", "platform spend", "risk",
                  "investment", "off-ramp", "milestone", "kpi",
                  "evaluation", "lighthouse"],
        rubric=["outcomes named in business terms (decision quality, not pipelines)",
                  "headcount justified by capability gap, not vanity",
                  "platform spend sized in ranges, not invented numbers",
                  "named risks with mitigation",
                  "explicit non-investments",
                  "12-month milestone ladder"],
        trap="headcount wishlist without sequencing or off-ramps",
    ),
    Question(
        qid="Q21", panelist="Rajesh Krishnan", round_label="R3",
        prompt=("A material data incident just happened. How do you communicate "
                "to the CEO and to customers? First hour, first day, first week."),
        keywords=["decision impact", "customer", "specific", "ack", "postmortem",
                  "prevention", "audit", "incident", "scope"],
        rubric=["CEO message leads with decision impact in business terms",
                  "customer comms specific: what data, what window, what action",
                  "cadence: ack <1h, status <24h, postmortem <1w",
                  "mentions prevention control with owner",
                  "doesn't hide behind technical jargon"],
        trap="vague reassurance ('we take data seriously')",
    ),
    Question(
        qid="Q23", panelist="Rajesh Krishnan", round_label="R3",
        prompt=("A high-performing leader on your team resists a governance "
                "standard you believe is non-negotiable. Walk me through the "
                "conversation."),
        keywords=["listen", "diagnose", "experiment", "floor", "non-negotiable",
                  "preserve trust", "escalate"],
        rubric=["listens first, diagnoses the source of resistance",
                  "separates resistance-to-policy-theater vs resistance-to-controls",
                  "names what the leader keeps (autonomy in HOW)",
                  "names the floor (WHAT) as non-negotiable",
                  "only escalates after showing they've heard",
                  "preserves both the team and the control"],
        trap=("capitulates to seniority OR over-applies without listening — "
              "both are wrong"),
    ),
]


# ---------------------------------------------------------------------------
# Scoring — keyword density + rubric criterion coverage
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Question metadata — sequence of expected concepts (in order)
# ---------------------------------------------------------------------------

# Each entry: ordered list of concept groups. Score is high when the answer
# mentions them in roughly this order, low when the order is reversed or
# concepts are missing. Groups are pipe-separated substrings (case-insensitive).
EXPECTED_SEQUENCE = {
    "Q1":  ["tenant_id", "kafka|lakehouse|ingestion", "slo", "ai"],
    "Q5":  ["idempot", "partition", "merge|dedup", "reconciliation"],
    "Q6":  ["isolation|partition|quota", "burst", "cost"],
    "Q9":  ["row_number|first_attempt", "lag", "nullif", "left join"],
    "Q11": ["skew|partition", "sink|backpressure", "gc", "rebalance"],
    "Q12": ["allow-list|allowlist|allowed", "tenant", "idempot", "audit",
            "abstain|confirmation"],
    "Q13": ["katalon|test execution|30k", "ai|data foundation", "now|inflection"],
    "Q15": ["federated", "domain|owner", "central|platform"],
    "Q19": ["decision latency", "trust|incident", "coverage|adoption"],
    "Q20": ["outcome", "headcount", "risk", "not invest|off-ramp"],
    "Q21": ["decision impact|customer", "ack|status|postmortem",
            "prevention|control"],
    "Q23": ["listen|diagnose", "floor|non-negotiable", "preserve trust"],
    "Q2":  ["not build|defer|trigger"],
}


def score_sequence(q: Question, a: str) -> float:
    """Did the candidate lay out concepts in a sensible order?

    For technical answers the right sequence is usually:
    constraint → mechanism → failure mode → trade-off.
    For strategy: stake → decision → criteria → risk.
    Returns 0..1 — fraction of present concepts that are in correct relative order.
    """
    seq = EXPECTED_SEQUENCE.get(q.qid, [])
    if not seq:
        return 1.0  # no sequence defined — neutral
    positions = []
    for group in seq:
        earliest = None
        for alt in group.split("|"):
            idx = a.find(alt)
            if idx >= 0 and (earliest is None or idx < earliest):
                earliest = idx
        positions.append(earliest)
    present = [p for p in positions if p is not None]
    if len(present) < max(2, len(seq) // 2):
        return 0.0
    in_order = sum(1 for a_, b in zip(present, present[1:]) if a_ < b)
    return in_order / max(1, len(present) - 1)


@dataclass
class Score:
    qid: str
    panelist: str
    coverage: float            # 0..1 — fraction of rubric criteria that appear addressed
    keyword_density: float     # 0..1 — fraction of expected keywords present
    length_score: int          # 0 / 1 — penalize too-short
    sequence_score: float      # 0..1 — does the answer follow the conceptual order?
    trap_handling: float       # -0.5..+0.3 — penalty for falling in, credit for rejecting
    raw: float                 # 0..4 final
    feedback: List[str] = field(default_factory=list)


def score_answer(q: Question, answer: str) -> Score:
    a = answer.lower().strip()
    feedback: List[str] = []

    # Length
    word_count = len(a.split())
    length_score = 1 if 60 <= word_count <= 600 else 0
    if word_count < 40:
        feedback.append("answer too short — under 40 words")
    if word_count > 700:
        feedback.append("answer very long — likely unfocused")

    # Keyword density
    hits = sum(1 for k in q.keywords if k in a)
    keyword_density = hits / len(q.keywords) if q.keywords else 0
    if keyword_density < 0.3:
        feedback.append(f"only {hits}/{len(q.keywords)} expected terms present — "
                        "likely missing the technical core")

    # Rubric coverage — heuristic: split rubric into single-sentence items,
    # award coverage if the candidate's answer contains any of the rubric's
    # key nouns/verbs. We extract key tokens (length>=5, lowercase, deduped).
    rubric_tokens = set()
    for r in q.rubric:
        for tok in re.findall(r"[a-z]{5,}", r.lower()):
            rubric_tokens.add(tok)
    rubric_hits = sum(1 for t in rubric_tokens if t in a)
    coverage = min(1.0, rubric_hits / max(6, len(rubric_tokens) // 2))
    if coverage < 0.4:
        feedback.append("rubric coverage low — likely missing required depth")

    # Sequence: does the answer follow the conceptual order?
    sequence_score = score_sequence(q, a)
    if sequence_score < 0.5 and EXPECTED_SEQUENCE.get(q.qid):
        feedback.append("answer sequence is disordered — concept ordering matters "
                       "(constraint → mechanism → failure → trade-off)")

    # Trap handling — three outcomes:
    #   (1) candidate doesn't engage with the trap pattern → no signal
    #   (2) candidate uses trap phrases AND rejects them → credit
    #   (3) candidate uses trap phrases AND concludes with them → penalty
    trap_handling = 0.0
    trap_words = re.findall(r"[a-z]{4,}", q.trap.lower())
    trap_hits = sum(1 for w in trap_words if w in a)
    negation_markers = ("not ", "don't ", "avoid ", "reject ", "wouldn't ",
                        "won't ", "never ", "fails ", "breaks ", "drifts in ",
                        "creates a bottleneck", "disagree ", "would not ",
                        "doesn't ")
    has_negation = any(m in a for m in negation_markers)
    if trap_hits >= 4 and has_negation:
        trap_handling = 0.3
        feedback.append("trap correctly rejected — good")
    elif trap_hits >= 4 and not has_negation:
        trap_handling = -0.5
        feedback.append("TRAP-LIKE: answer matches a known weak pattern — "
                       "see rubric above")

    # Final raw score 0..4 (rubric from README §20)
    raw = 0.0
    raw += 0.8 * keyword_density        # technical core present
    raw += 1.2 * coverage               # rubric satisfied
    raw += 0.4 * length_score            # reasonable depth
    raw += 0.4 * sequence_score          # ordered reasoning
    raw += trap_handling                 # penalty or credit
    raw = max(0.0, min(4.0, raw))

    return Score(
        qid=q.qid,
        panelist=q.panelist,
        coverage=round(coverage, 2),
        keyword_density=round(keyword_density, 2),
        length_score=length_score,
        sequence_score=round(sequence_score, 2),
        trap_handling=trap_handling,
        raw=round(raw, 2),
        feedback=feedback,
    )


# ---------------------------------------------------------------------------
# Loop — interactive or demo
# ---------------------------------------------------------------------------

def ask(q: Question) -> str:
    print()
    print("=" * 78)
    print(f"  {q.panelist} ({q.round_label}) — {q.qid}")
    print("=" * 78)
    print(textwrap.fill(q.prompt, 78, subsequent_indent="  "))
    print()
    print("(paste/type your answer; finish with a line containing only 'END')")
    print()
    buf: List[str] = []
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        if line.strip() == "END":
            break
        buf.append(line)
    return "\n".join(buf).strip()


def run_interactive() -> List[Score]:
    scores: List[Score] = []
    # Order: R1 panel, R2, R3 (12 questions — picks the most discriminating)
    panel_qs = {p.name: [q for q in QUESTION_BANK if q.panelist == p.name]
               for p in PANEL}
    order = ["Vu Bui", "Que Tran", "Son Dao", "Duke Nguyen", "Rajesh Krishnan"]
    for name in order:
        for q in panel_qs[name]:
            ans = ask(q)
            if not ans:
                print("(no answer — skipping)")
                continue
            s = score_answer(q, ans)
            scores.append(s)
            print(f"\n  → score: {s.raw}/4  (coverage {s.coverage}, "
                  f"keywords {s.keyword_density})")
            if s.feedback:
                for f in s.feedback:
                    print(f"     • {f}")
    return scores


def run_demo() -> List[Score]:
    """Worked example: a candidate with mixed answers — strong on some,
    weak on others. Prints scores and recommendations."""
    print("\n=== DEMO RUN — sample candidate answers ===\n")

    # Synthetic answers — alternating strong/weak so the scorecard is illustrative
    demo_answers = {
        "Q1": (  # Vu Bui — strong (ordered: tenant → mechanism → SLO → AI)
            "Tenant isolation is the spine, not an afterthought — tenant_id in "
            "every key, partition, index, audit row. At 30k tenants and "
            "~46k events/sec peak I would use Kafka for ingestion with "
            "idempotent producers, durable lakehouse on S3 + Iceberg for 3-"
            "year history, DynamoDB for hot run status, and a certified "
            "warehouse + semantic layer for executive KPIs. SLOs sit on "
            "data products, not on infra — a dashboard SLO is owned by the "
            "domain. The AI plane consumes governed products, never scrapes "
            "arbitrary stores. Eval first, retrieval second, model third — "
            "the retrieval harness is a deployment gate, not an experiment."),
        "Q2": (  # Vu Bui — weak (no triggers, no specific non-builds)
            "I would not build things that are not core to the role."),
        "Q5": (  # Que Tran — strong
            "Edge dedup on event_id, idempotent producers, stable partition "
            "key = hash(tenant_id, execution_id). Kafka for durable replay, "
            "silver merge keyed by business grain using aggregate_version for "
            "ordering. Reconciliation against producer manifest counts. "
            "Quarantine poison records, never silent drop. Schema registry "
            "rejects breaking changes. Per-tenant cost attribution."),
        "Q9": (  # Son Dao — strong
            "Window: ROW_NUMBER over partition (tenant, project, test, env, "
            "execution) ordered by attempt_id — gives first_attempt. LAG over "
            "(tenant, project, test, env) ordered by completed_at, "
            "execution_id gives previous_status for transitions. AVG(IFF(...)) "
            "with NULLIF for divide-by-zero. LEFT JOIN recovery CTE so stable "
            "tests aren't dropped. environment_hash is a tradeoff — fragments "
            "data but separates environments. In production I'd add "
            "shrinkage and partition prune on dt."),
        "Q12": (  # Son Dao — weak
            "I would put safety controls around the agent and let it edit "
            "tests carefully."),
        "Q15": (  # Duke Nguyen — strong
            "Federated ownership with a central platform team. Domains own "
            "metric definitions and source contracts; central team owns "
            "ingestion, catalog, policy, observability, paved road. Centralized "
            "creates a bottleneck; embedded drifts in standards. Federated "
            "fails if central team doesn't provide a paved road — that's the "
            "first thing to build."),
        "Q20": (  # Rajesh Krishnan — strong
            "12-month outcomes: certified metrics for top 5 executive "
            "decisions with zero silent material errors, ingestion + "
            "lakehouse with SLOs covering ≥80% of accepted events, one AI "
            "lighthouse with held-out eval harness and production canary, "
            "governed AI context plane. Headcount: 1 senior platform lead, "
            "2 platform engineers, 1 analytics engineer, 1 applied ML/eval "
            "engineer, 0.5 governance engineer paired with security. Risks: "
            "hiring slips (staged org), AI eval can't reach bar (ship eval + "
            "deterministic baseline first), governance slows Engineering "
            "(measure lead time, walk back any that hurts it). NOT investing: "
            "real-time OLAP until latency tests prove needed, data mesh, "
            "top-down BI consolidation."),
        "Q23": (  # Rajesh Krishnan — partial (good direction, weak on listening)
            "I'd preserve the standard but coach the leader. Most resistance "
            "is signal about policy theater, but the floor is non-negotiable. "
            "I'd escalate if they refused after explanation."),
    }

    scores: List[Score] = []
    panel_qs = {p.name: [q for q in QUESTION_BANK if q.panelist == p.name]
               for p in PANEL}
    for p in PANEL:
        for q in panel_qs[p.name]:
            ans = demo_answers.get(q.qid, "")
            if not ans:
                continue
            s = score_answer(q, ans)
            scores.append(s)
            print(f"  {q.qid}  panelist={q.panelist:<22}  "
                  f"score={s.raw}/4   coverage={s.coverage}   "
                  f"keywords={s.keyword_density}")
            if s.feedback:
                for f in s.feedback:
                    print(f"        - {f}")
    return scores


def print_scorecard(scores: List[Score]) -> None:
    print()
    print("=" * 78)
    print("  PER-PANELIST SCORECARD")
    print("=" * 78)
    by_panelist: dict = {}
    for s in scores:
        by_panelist.setdefault(s.panelist, []).append(s.raw)
    for p in PANEL:
        vals = by_panelist.get(p.name, [])
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        bar = "█" * int(round(avg * 8))
        print(f"  {p.name:<22}  avg={avg:>4.2f}/4  ({len(vals)} qs)  {bar}")

    overall = sum(s.raw for s in scores) / max(1, len(scores))
    print()
    print(f"  OVERALL: {overall:.2f}/4")
    if overall >= 3.2:
        print("  Verdict: Head-level exceptional — ready for onsite.")
    elif overall >= 2.5:
        print("  Verdict: Strong — tighten weakest round before onsite.")
    elif overall >= 1.8:
        print("  Verdict: Partial — practice rounds 2 and 3 with mock partner.")
    else:
        print("  Verdict: Weak — re-run pack from scratch, focus on rubric criteria.")

    # Top 3 weakest questions to drill
    weakest = sorted(scores, key=lambda s: s.raw)[:3]
    if weakest:
        print()
        print("  Drill these next:")
        for s in weakest:
            print(f"    • {s.qid} ({s.panelist}) — {s.raw}/4")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true",
                    help="run a worked example with synthetic answers")
    args = ap.parse_args()

    if args.demo:
        scores = run_demo()
        print_scorecard(scores)
        return

    print("Katalon Head of Data — Mock Interview Simulator")
    print("=================================================")
    print(f"{len(PANEL)} panelists, {len(QUESTION_BANK)} questions in bank.")
    print("Type your answer for each; finish with a line containing only 'END'.")
    print("(Tip: run with --demo first to see what a scorecard looks like.)\n")

    scores = run_interactive()
    print_scorecard(scores)


if __name__ == "__main__":
    main()