# Course flow diagrams — the 4-phase journey

> **If you can read a flowchart, you can read this course.** Each diagram is a picture of one phase, drawn like a 4th-grade teacher would draw it: boxes, arrows, plain words.

---

## The big picture (all 4 phases)

```
                     THE AI FDE JOURNEY
                     ==================

   "I wrote a tool"        "the tool is a          "it runs 24/7       "it's a platform
                           service"               for everyone"       the team extends"
        │                       │                       │                     │
        ▼                       ▼                       ▼                     ▼
   ┌─────────┐             ┌──────────┐            ┌──────────┐          ┌──────────┐
   │ PHASE 1 │ ──────────▶ │ PHASE 2  │ ────────▶ │ PHASE 3  │ ───────▶ │ PHASE 4  │
   │Founda-  │             │ Core     │            │ Deploy-  │          │ Capstone │
   │tions    │             │ Build    │            │ ment     │          │          │
   └─────────┘             └──────────┘            └──────────┘          └──────────┘
   1 week                  2 weeks                 2 weeks               4 weeks
   • CLI tool              • FastAPI service       • Circuit breaker     • MCP tools
   • 1-pager               • RAG                   • Rate limiter        • Multi-agent
   • Sample emails         • Eval harness          • Hybrid retrieval    • Distilled SLM
   • Solution outline      • Docker                • Runbook + RACI      • 5 case studies
   • 5 questions           • 13 pytest ✓           • On-call rotation    • Portfolio
   • Style guide           • 3 docs (PRD,etc)      • 3-loop cadence      • Capstone demo
   • Tracker data          • 3 ADRs                • 13 pytest ✓         • 4 projects ✓
```

**The pattern:** every phase takes what the last phase made and makes it *better, stronger, more real*. Like a Pokemon evolving. Phase 1 = the egg. Phase 4 = the fully evolved thing.

---

## Phase 1: Foundations (the egg)

```
    WHAT YOU START WITH
    ===================

    Customer email: "Where is my parcel PF-1003?"
                    │
                    ▼
    ┌──────────────────────────────┐
    │   Phase 1 CLI tool           │
    │   (runs in Mei's terminal)   │
    │                              │
    │   reads shipments.json       │
    │   reads style-guide.md       │
    │   asks the LLM for a draft   │
    │   prints the draft           │
    └──────────────────────────────┘
                    │
                    ▼
    Draft: "Hi! Your parcel PF-1003 is in customs."

    PROBLEM: only Mei can use it. It lives on her laptop.
```

**The story:** Mei builds a Python script that reads the tracker, looks at the style guide, and asks the LLM "write me a draft reply." It works on her laptop. But only on her laptop.

---

## Phase 2: Core Build (the service)

```
    WHAT YOU BUILD
    ==============

    Customer email: "Where is my parcel?"
                    │
                    ▼
    ┌──────────────────────────────┐
    │   FastAPI service            │  ◀── anyone on the team
    │   (runs on Daniel's VM)      │      can call this now
    │                              │      (no laptop needed)
    │   GET  /health               │
    │   POST /draft                │  ◀── the same Mei-call,
    │   POST /retrieve             │      but over HTTP
    │   POST /eval                 │  ◀── grades itself
    └──────────────────────────────┘
        │           │           │
        │           │           │
        ▼           ▼           ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │Mock    │ │Mock    │ │30-row  │
    │LLM     │ │store   │ │eval    │
    │back-   │ │(token  │ │set     │
    │end     │ │overlap)│ │        │
    └────────┘ └────────┘ └────────┘

    YOU ALSO WRITE (the docs that justify the service):
    • discovery-deck.md     (what we heard from the customer)
    • pacificfreight-prd.md (what we're building)
    • pacificfreight-design.md (how we're building it)
    • 0001-fastapi.md ADR   (why FastAPI and not Flask)
    • 0002-mock-store.md    (why a mock store and not Pinecone)
    • 0003-regression-5%.md (why we trip on 5% drop)

    AT THE END: 13/13 pytest cases pass. Service runs in Docker.
```

**The story:** Same drafter, but now wrapped in a web service. Anyone at PacificFreight can call it from their browser, not just Mei. The service has its own tests. The customer has the docs to read about why the service is built the way it is.

---

## Phase 3: Deployment (the safety net)

```
    WHAT CHANGES
    ============

    Customer email
         │
         ▼
    ┌──────────────────────────────┐
    │  FastAPI service (Phase 2)   │
    │  + Phase 3 hardening:        │
    │                              │
    │  ⚡ /draft/stream     (SSE)  │  ◀── Mei sees the first
    │  👍 /feedback         (rate) │      word in 200ms, not 1.8s
    │  📊 /metrics     (Prometheus)│
    │  🛡 /circuit/state    (live) │
    └──────────────────────────────┘
         │              │              │
         │              │              │
         ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ HYBRID   │  │ CIRCUIT  │  │  CADDY   │
    │ RETRIEVER│  │ BREAKER  │  │ (TLS +   │
    │          │  │          │  │  rate-   │
    │ BM25 +   │  │ if OpenAI│  │  limit   │
    │ dense +  │  │ is down  │  │  at the  │
    │ RRF      │  │ for 30s, │  │  edge)   │
    │          │  │ fall back│  │          │
    │ beats    │  │ to last  │  │          │
    │ the mock │  │ good     │  │          │
    │ store    │  │ cached   │  │          │
    │          │  │ answer   │  │          │
    └──────────┘  └──────────┘  └──────────┘

    OPS ARTIFACTS (the docs that survive the FDE's exit):
    • runbook.md             "What to do at 2am"
    • raci.md                "Who decides what"
    • on-call-rotation.md    "Whose phone rings"

    CONSULTING ARTIFACTS:
    • stakeholder-map.md     3+1 audiences, decision matrix
    • iteration-cadence.md   3-loop Mon daily/weekly/monthly
    • 5-question handoff test  "FDE has left" — pass/fail

    AT THE END: 13/13 pytest ✓. Survives an OpenAI outage.
```

**The story:** The service is now "production-grade." It has a safety net for when OpenAI goes down, a rate limiter so Mei can't accidentally burn $50, a PII redactor so customer emails don't leak into logs, a hybrid retriever that catches queries the mock store missed, and a feedback loop so Mei's thumbs-up/down flows back into next Monday's iteration. Plus three docs (runbook, RACI, on-call) that let a new FDE take over the engagement on day 1.

---

## Phase 4: Capstone (the platform)

```
    WHAT YOU BUILD ON TOP
    =====================

    Phase 3 service
         │
         ├──── Project 1: MCP ──────────────┐
         │     (Mei adds tools:              │
         │      refund, translate,           │
         │      escalate — without           │
         │      re-deploying)                │
         │                                  │
         ├──── Project 2: Multi-agent ──────┤
         │     (complex multi-shipment       │
         │      cases handled by 3 agents:   │
         │      Mei, Sarah, Daniel)          │
         │                                  │
         └──── Project 3: Distilled SLM ─────┤
               (Qwen 1.5B trained on          │
                Mei's drafts, 5% of GPT's      │
                cost, 91% of its quality)      │
                                              │
         ┌──── Project 4: Fresh engagement ──┤
         │     (a NEW customer, a NEW        │
         │      domain — the AI Data         │
         │      Analyst, code sandbox)       │
         │                                  │
         ├──── 5 case studies ──────────────┤
         │     (PF drafter, PIVOT, postmortem,│
         │      SLM cost, handoff)            │
         │                                  │
         └──── Portfolio + capstone demo ───┘
               (the 10-min presentation to
                the evaluation panel)
```

**The story:** Phase 3 made the service survive the customer. Phase 4 makes the service a **platform** the team can extend without the FDE. MCP means new tools can be added without re-deploying. Multi-agent means complex cases (multi-shipment) are handled end-to-end. The SLM means the cost ceiling stays at $5/month even at 10× growth. Project 4 (the AI Data Analyst) is a fresh engagement — a new customer, a new domain — to prove the FDE pattern transfers. The 5 case studies + portfolio + capstone presentation are the artifacts the FDE takes to a job interview.

---

## Why this matters (the FDE lens)

```
    MOST AI PROJECTS DIE HERE:
    ══════════════════════════

    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
    │ Demo │ ─▶ │ Pilot│ ─▶ │ "Who │ ─▶ │ ...  │
    │ works│    │ works│    │ owns │    │ dead │
    └──────┘    └──────┘    │this?"│    └──────┘
                            └──────┘
                                │
                                ▼
                          (no answer)
                                │
                                ▼
                          (no one runs it)
                                │
                                ▼
                          (it dies)


    THIS COURSE TEACHES YOU TO GO HERE INSTEAD:
    ════════════════════════════════════════════

    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
    │ Demo │ ─▶ │ Pilot│ ─▶ │Prod  │ ─▶ │Plat- │ ─▶ │Exit  │
    │ works│    │ works│    │grade │    │form  │    │clean │
    └──────┘    └──────┘    └──────┘    └──────┘    └──────┘
       │           │           │           │           │
    Phase 1     Phase 2     Phase 3     Phase 4     handoff
    foun-       core        deploy-     cap-        test
    dations     build       ment        stone       passes
```

**The story:** Most AI projects die at "Who owns this?" because no one wrote the runbook. This course teaches you to write the runbook, the RACI, the iteration cadence, the 5-question handoff test. By the end, the customer can fire you and the system keeps running. **That is the FDE's job.**

---

## How long does the whole course take?

| Phase | What | Time |
|---|---|---|
| 1 | Foundations (CLI + brief) | 1 week |
| 2 | Core Build (service + docs) | 2 weeks |
| 3 | Deployment (production) | 2 weeks |
| 4 | Capstone (platform + portfolio) | 4 weeks |
| **Total** | | **~9 weeks** |

That's about 2 months full-time, or 4-5 months part-time. By the end, you have: a working service, a portfolio of 4 projects, 5 case studies, and a capstone presentation. Enough to walk into a job interview and say "I build AI services that survive the customer."
