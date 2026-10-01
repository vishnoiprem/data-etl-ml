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

@dataclass
class Score:
    qid: str
    panelist: str
    coverage: float            # 0..1 — fraction of rubric criteria that appear to be addressed
    keyword_density: float     # 0..1 — fraction of expected keywords present
    length_score: int          # 0 / 1 — penalize too-short
    penalty: float             # 0..0.5 — for hitting the 'trap' pattern
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

    # Trap penalty: if the candidate's answer matches the trap pattern
    # keywords heavily, apply a penalty.
    penalty = 0.0
    trap_words = re.findall(r"[a-z]{4,}", q.trap.lower())
    trap_hits = sum(1 for w in trap_words if w in a)
    if trap_hits >= 3:
        penalty = 0.5
        feedback.append("TRAP-LIKE: answer matches a known weak pattern — "
                       "see rubric above")

    # Final raw score 0..4 (rubric from README §20)
    raw = 0.0
    raw += 1.0 * keyword_density        # technical core present
    raw += 1.5 * coverage               # rubric satisfied
    raw += 0.5 * length_score            # reasonable depth
    raw -= penalty
    raw = max(0.0, min(4.0, raw))

    return Score(
        qid=q.qid,
        panelist=q.panelist,
        coverage=round(coverage, 2),
        keyword_density=round(keyword_density, 2),
        length_score=length_score,
        penalty=penalty,
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
        "Q1": (  # Vu Bui — strong
            "Three planes: business BI for executives, product data plane for "
            "test executions (20M result-rows/day, ~46k events/sec peak), and "
            "an AI plane for retrieval and eval. Tenant ID everywhere. Hot "
            "serving in DynamoDB for live run status, durable lakehouse on S3 "
            "+ Iceberg for 3-year history, certified warehouse + semantic layer "
            "for executive KPIs. AI plane consumes governed products, never "
            "scrapes arbitrary stores. Eval first, retrieval second, model "
            "third. SLOs on data products, not just infra. Reconciliation "
            "between producer, accepted, silver, and served counts."),
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