# AI FDE — Phase 3: Deployment & Reliability

> **From a working service to a production system with a team that owns it.** Three lessons per track + three ops artifacts. ~2 weeks of study. Builds on the Phase 2 service in `../phase-2-core-build/`.

An **AI FDE at the Phase 3 level** can take a service that works on a laptop and turn it into a system that survives the customer. The drafter is no longer "Mei's tool" — it is a **platform** with a runbook, a RACI, an on-call rotation, a 3-loop iteration cadence, and a stakeholder map that signs off on changes. The FDE's job in Phase 3 is to **make themselves unnecessary** by the end of the phase.

---

## What you will produce by the end of Phase 3

1. **A production-grade service** — the Phase 2 FastAPI service is hardened with: hybrid retrieval (BM25 + dense + RRF), a circuit breaker, token-bucket rate limiting, in-process redaction, Prometheus telemetry, streaming `/draft/stream`, a `/feedback` endpoint, a GO/NO-GO regression gate, and a Caddy reverse proxy in front of it.
2. **Three ops artifacts** that survive the FDE's exit:
   - `consulting/runbook.md` — the SEV-1/2/3 playbook (Daniel owns)
   - `consulting/raci.md` — who decides what (Sarah owns)
   - `consulting/on-call-rotation.md` — the pager (Daniel owns)
3. **Three consulting lessons** that close the 3 stakeholder loops:
   - C1: stakeholder map (3 + 1 audiences, decision-rights matrix, GO/NO-GO criteria)
   - C2: iteration cadence (the 3-loop rhythm that keeps the drafter fresh)
   - C3: ownership handoff (the 5-question "FDE has left" test)

Phase 3 is **not** Kubernetes, **not** a frontend, **not** a multi-tenant SaaS. It is the smallest lift that takes a working service and turns it into a system a 12-person SMB can actually run.

---

## The scenario (continued from Phase 2)

Same customer — **PacificFreight Co.**, the 12-person cross-border logistics SMB — with one lift:

> The Phase 2 service answers "where is my parcel?" reliably in mock mode. Phase 3 lifts this: the service is now **deployed in production**, with a hybrid retriever that beats the mock store on real chunks, a circuit breaker that survives a 10-minute OpenAI outage, a redactor that strips PII from logs, telemetry that exposes a `/metrics` endpoint, and a feedback loop where Mei's thumbs-up/down flows back into the next Monday's iteration.

Read the lift: [`scenario-lift.md`](./scenario-lift.md).
The Phase 2 service that this phase hardens: [`../phase-2-core-build/service/`](../phase-2-core-build/service/).
The Phase 1 brief that started it all: [`../phase-1-foundations/scenario-brief.md`](../phase-1-foundations/scenario-brief.md).

---

## Two parallel tracks

| Track | What you learn | What you produce | Files |
|---|---|---|---|
| **Technical** | Hybrid retrieval, streaming, circuit breakers, rate limiting, redaction, telemetry, eval-in-CI | A production-deployed service with 13 pytest cases green | [`technical/`](./technical/) + the Phase 2 service in `../phase-2-core-build/service/` |
| **Consulting** | Stakeholder maps, RACI, runbooks, iteration cadence, ownership handoff | A stakeholder map, an iteration cadence, a runbook, a RACI, an on-call rotation, a 5-question handoff test | [`consulting/`](./consulting/) |

You can take the tracks in either order, but the **end-of-phase deliverable** is the same artifact seen from two sides: the **service in production** (technical) and the **team that owns it** (consulting).

See:
- [TECHNICAL-TRACK.md](./TECHNICAL-TRACK.md) — the 3-lesson map
- [CONSULTING-TRACK.md](./CONSULTING-TRACK.md) — the 3-lesson map

---

## The standard template (carried over from Phase 1 and 2)

### Technical lesson (.md + .py)

Each Phase 3 technical lesson is **two files**:

- **`technical/NN-name.md`** — the lesson narrative: 🎯 Outcome / 🧠 Mindset / 🛠️ Practice / 🏛️ FDE Lens / 🌙 Reflect.
- **`technical/NN-name.py`** — the runnable hands-on script. **The .py is the spec.** If the .py doesn't run, the lesson isn't done.

The recommended sequence is **T1 → T2 → T3**, because each builds on the last:

```
T1 (Advanced retrieval — BM25 + dense + RRF)
   ↓ retriever now beats mock on real chunks
T2 (Eval, monitoring, iteration)
   ↓ /feedback + /metrics + 3-loop Monday cadence
T3 (Scale, reliability, security)
   ↓ circuit breaker + rate limiter + redactor + Caddy
```

### Consulting lesson (.md) + ops artifacts (.md)

```
C1 (Stakeholder alignment)
   ↓ stakeholder map + GO/NO-GO criteria → "go"
C2 (Delivery planning & iteration)
   ↓ 3-loop Monday cadence + the iteration report
C3 (Ownership handoff)
   ↓ runbook + RACI + on-call rotation + 5-question "FDE has left" test
```

The ops artifacts (`runbook.md`, `raci.md`, `on-call-rotation.md`) live in `consulting/` alongside the lessons. They're the artifacts the FDE hands to the customer.

---

## File layout

```
phase-3-deployment/
├── README.md                          ← you are here
├── scenario-lift.md                   ← the Phase 2→3 narrative
├── TECHNICAL-TRACK.md                 ← 3-lesson map for the technical track
├── CONSULTING-TRACK.md                ← 3-lesson map for the consulting track
├── technical/                         ← 3 lessons (.md + .py each)
│   ├── 01-advanced-retrieval.{md,py}
│   ├── 02-eval-monitoring-iteration.{md,py}
│   └── 03-scale-reliability-security.{md,py}
└── consulting/                        ← 3 lessons + 3 ops artifacts
    ├── 01-stakeholder-alignment.md
    ├── 02-delivery-iteration.md
    ├── 03-ownership-handoff.md
    ├── runbook.md                     ← ops artifact (Daniel owns)
    ├── raci.md                        ← ops artifact (Sarah owns)
    └── on-call-rotation.md            ← ops artifact (Daniel owns)
```

The **service code itself** lives in [`../phase-2-core-build/service/`](../phase-2-core-build/service/). Phase 3 hardens that service in place — it does not move the code. The 13 pytest cases there (`../phase-2-core-build/service/tests/`) are the regression suite that gates every Phase 3 change.

---

## How long does this take?

| Track | Time per lesson | Total |
|---|---|---|
| Technical | 45 min (read + run the .py) | ~2.5 hours |
| Consulting | 30–35 min (read + write the deliverable) | ~1.5 hours |
| **Both tracks** | — | **~4 hours** |

The hardest part of Phase 3 is not the code — it's writing the **ops artifacts**. The runbook is the document that gets used at 2am during a SEV-1. If it's not specific enough to be actionable, it's not a runbook.

---

## What comes next

When you finish Phase 3 you have a service that:
- Passes 13/13 pytest cases (the Phase 2 baseline)
- Has a circuit breaker, rate limiter, redactor, cache, tiered fallback
- Has a hybrid retriever (BM25 + dense + RRF) that beats the mock store
- Exposes `/metrics` and `/circuit/state` for the ops dashboard
- Streams drafts via `/draft/stream`
- Collects thumbs-up/down via `/feedback`
- Is documented in a runbook + RACI + on-call rotation
- Has a 5-question "FDE has left" test that a new FDE passes on day 1

**That's the bar.**

Phase 4 (in `../phase-4-capstone/`) takes the Phase 3 service and turns it into a **platform**: MCP for tool use, multi-agent for complex cases, a distilled SLM for cost, a fresh engagement for breadth, plus 5 case studies and a capstone presentation.

Read [`../phase-4-capstone/scenario-brief.md`](../phase-4-capstone/scenario-brief.md) for the Phase 4 lift.
