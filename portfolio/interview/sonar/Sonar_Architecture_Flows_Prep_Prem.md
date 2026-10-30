# Sonar — Data & Agentic Director — Architecture Flows Prep (Prem Vishnoi)

> For Round 4 (Technical Assessment) and deep-dive technical discussions. Each architecture is a **flow you can draw on a whiteboard and explain out loud**. Practice sketching 2-3 of these from memory.
>
> Three buckets:
> 1. **Sonar's domain** — so you speak their product language fluently
> 2. **Your real systems** — framed as interview talking points
> 3. **System-design answers** — what to draw if asked to design live

---

# PART 1 — SONAR'S DOMAIN ARCHITECTURES
*(Speak their language — shows you understand the product before day 1)*

## 1.1 Code Verification Pipeline (Sonar's core: SonarQube)

```
┌──────────┐   ┌───────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────┐
│  Source  │──▶│  Ingest / │──▶│   Parse →    │──▶│   Analysis    │──▶│  Results │
│  (Git /  │   │  Trigger  │   │   AST / CFG  │   │   Engine      │   │  Store   │
│  PR /CI) │   │ (webhook) │   │              │   │ (rules+ML)    │   │          │
└──────────┘   └───────────┘   └──────────────┘   └───────────────┘   └────┬─────┘
                                                          │                  │
                                              ┌───────────┴──────┐    ┌──────▼──────┐
                                              │ Bugs / Vulns /   │    │  Dashboard  │
                                              │ Code Smells /    │    │  + API +    │
                                              │ Security Hotspots│    │  PR comment │
                                              └──────────────────┘    └─────────────┘
```

**Talk track (how you explain it):**
1. **Trigger** — commit/PR fires a webhook; CI pipeline calls the analyzer.
2. **Parse** — code → Abstract Syntax Tree (AST) + Control Flow Graph (CFG) per language.
3. **Analysis** — rules engine (taint analysis, data-flow, pattern matching) plus ML for ranking/triage. Finds bugs, vulnerabilities, code smells, security hotspots.
4. **Results** — stored, surfaced as PR comments, dashboards, quality gates that **block merge** if thresholds fail.
5. **Key properties:** independent, explainable, consistent — Sonar's three words. Every finding must be **explainable** (why it's flagged), not a black box.

---

## 1.2 The Agent-Centric Development Cycle (AC/DC) — Sonar's thesis

```
        ┌────────────────────────────────────────────────────────┐
        │                                                        │
        ▼                                                        │
┌───────────────┐    ┌──────────────┐    ┌──────────────────┐    │
│  AI Agent     │    │   Generated  │    │  Sonar           │    │
│ (Claude Code, │───▶│   Code       │───▶│  Verification    │────┤
│  Copilot,     │    │              │    │  (independent)   │    │
│  Devin, etc.) │    └──────────────┘    └────────┬─────────┘    │
└───────────────┘                                 │              │
        ▲                                  ┌───────▼────────┐     │
        │                                  │ Pass? ─Yes─▶ Merge   │
        │                                  │   │                  │
        └──────────── Feedback ────────────┘  No → fix & retry ──┘
        (explainable findings the agent can act on)
```

**Talk track:**
- AI agents write code fast but can't be trusted blindly — they hallucinate, introduce subtle security/logic flaws, and lack project context.
- Sonar is the **independent verification layer** in the loop — the agent's "code reviewer that never sleeps."
- **Critical insight (your edge):** the feedback must be *machine-readable and explainable* so the agent can self-correct. This is the Foundation Agent (agentic repair) + Context Augmentation (giving agents the constraints they need).
- **Your bridge:** "This is exactly the guardrail loop I built for Text-to-SQL — generate, verify against schema/rules, feed back errors, retry. Sonar does it at code scale."

---

## 1.3 Context Augmentation / RAG for Agents (SonarSweep + Context)

```
┌──────────────┐
│  Codebase    │──┐
│  + Standards │  │   ┌─────────────┐    ┌──────────────┐
│  + History   │  ├──▶│  Embed +    │───▶│  Vector +    │
└──────────────┘  │   │  Index      │    │  Graph Store │
┌──────────────┐  │   └─────────────┘    └──────┬───────┘
│  Rules /     │──┘                             │
│  Constraints │                                │ retrieve relevant
└──────────────┘                                │ context
                                                ▼
┌───────────────┐    ┌──────────────────┐   ┌─────────────────┐
│  Agent asks/  │───▶│  Retrieval +     │──▶│  Agent gets     │
│  writes code  │    │  Constraint inj. │   │  grounded,      │
└───────────────┘    └──────────────────┘   │  in-context code│
                                            └─────────────────┘
```

**Talk track:** Agents are only as good as their context. Sonar feeds them enterprise-grade context (codebase conventions, constraints, prior decisions) via retrieval + a knowledge graph — so generated code fits the project, not just generic patterns. **This is RAG applied to code** — you've built RAG/embedding systems (item matching, Text-to-SQL), so you understand it natively.

---

# PART 2 — YOUR REAL SYSTEMS (interview talking points)

## 2.1 Makro Databricks Lakehouse (Medallion Architecture)

```
SOURCES                  INGEST              LAKEHOUSE (Delta)          SERVE
┌──────────┐         ┌────────────┐    ┌──────────────────────┐   ┌──────────┐
│ Finance  │         │  Batch +   │    │ BRONZE (raw)         │   │ 50+ Exec │
│ Supply   │────────▶│  Streaming │───▶│   ↓ clean/validate   │──▶│ Dashboards│
│ Retail   │         │  ingestion │    │ SILVER (conformed)   │   │ (Power BI)│
│ E-comm   │         │            │    │   ↓ business logic   │   │          │
└──────────┘         └────────────┘    │ GOLD (curated/marts) │   ├──────────┤
                                       └──────────┬───────────┘   │ ML / AI  │
                                                  │               │ Pricing, │
                                  10B+ rows/day    │               │ Forecast │
                                                  └──────────────▶│ Text2SQL │
                                                                  └──────────┘
```

**Talk track:** "I modernised legacy systems into a Databricks Lakehouse processing 10B+ rows/day. Medallion layers — Bronze raw, Silver conformed, Gold curated marts — gave us one trusted source for BI, ML, and real-time. That foundation is what cut month-end close from 5 days to 2 hours and powered 50+ exec dashboards."

**Architecture decisions to discuss:** Delta Lake (ACID on the lake), why Lakehouse over separate warehouse+lake (one copy, lower cost, ML + BI together), reusable patterns enabling fast multi-country expansion.

---

## 2.2 Lazada Real-Time Platform (Streaming)

```
┌─────────┐   ┌─────────┐   ┌──────────────┐   ┌─────────────┐   ┌────────────┐
│ Orders  │   │  Kafka  │   │    Flink     │   │ ClickHouse  │   │ Last-mile  │
│ Traffic │──▶│ (events)│──▶│  (stream     │──▶│  (OLAP) +   │──▶│ logistics  │
│ Driver  │   │ 100M+/d │   │  processing) │   │  HBase (KV) │   │ analytics  │
│telemetry│   └─────────┘   └──────────────┘   └─────────────┘   │ 20M+ insights/d│
└─────────┘                                                      └────────────┘
```

**Talk track:** "At Lazada I architected a real-time platform — Kafka for ingestion at 100M+ events/day, Flink for stream processing, ClickHouse for OLAP queries, HBase for low-latency key-value lookups. It powered last-mile logistics analytics generating 20M+ daily insights and improved delivery routing. Earned a double promotion for the impact."

**Decisions to discuss:** Flink vs Spark Streaming (true streaming, lower latency, event-time/windowing), ClickHouse for fast aggregations vs HBase for point lookups — the right tool per access pattern.

---

## 2.3 Text-to-SQL GenAI (your strongest agentic/guardrail story) 🔑

```
┌──────────┐   ┌─────────────────┐   ┌──────────────┐   ┌──────────────┐
│ Business │   │  Semantic Layer │   │     LLM      │   │  GUARDRAILS  │
│ user NL  │──▶│  + Schema       │──▶│  generates   │──▶│  validate:   │
│ question │   │  understanding  │   │  SQL         │   │ - schema ok? │
└──────────┘   │  (RAG context)  │   └──────────────┘   │ - safe? read-│
               └─────────────────┘                      │   only?      │
                                                        │ - row limits │
                                          ┌─────────────┴──────────────┘
                                          │
                              Pass ───────┼─────── Fail
                                ▼                    ▼
                        ┌──────────────┐    ┌─────────────────┐
                        │ Execute →    │    │ Block / re-prompt│
                        │ return result│    │ with error ctx   │
                        └──────────────┘    └─────────────────┘
```

**Talk track (this maps DIRECTLY to Sonar's verification loop):** "I built a Text-to-SQL platform so non-technical users query data in natural language. The LLM generating SQL was the easy part — the hard part was guardrails: schema validation, read-only enforcement, row limits, and re-prompting with error context when the SQL was wrong. That generate → verify → feedback → retry loop is structurally identical to what Sonar does for AI-generated code. I've already lived this problem."

---

# PART 3 — SYSTEM DESIGN ANSWERS (what to draw if asked live)

## 3.1 "Design a scalable code-analysis / verification platform"

**Step 1 — Clarify (always ask first):**
- Scale? (repos, commits/day, languages, latency target)
- Sync (block PR) or async? Multi-tenant SaaS or single-org?
- Full scan vs incremental?

**Step 2 — Draw the architecture:**

```
                    ┌──────────────────────────────────────────┐
                    │              CONTROL PLANE                │
                    │  Auth · Tenant mgmt · Config · Quality    │
                    │           Gates · Rules registry          │
                    └──────────────────────────────────────────┘
┌─────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────────┐   ┌───────────┐
│ Git /CI │──▶│ API GW + │──▶│   Queue     │──▶│  Analysis    │──▶│ Results   │
│ webhook │   │ Ingest   │   │ (Kafka/SQS) │   │  Workers     │   │ Store +   │
└─────────┘   └──────────┘   └─────────────┘   │ (autoscale,  │   │ Object    │
                                  │            │ lang-specific│   │ storage   │
                            ┌─────▼──────┐     │ analyzers)   │   └─────┬─────┘
                            │ Incremental│     └──────┬───────┘         │
                            │ cache (only│            │            ┌────▼─────┐
                            │ changed    │◀───────────┘            │ Dashboard│
                            │ files)     │                         │ API · PR │
                            └────────────┘                         │ comments │
                                                                   └──────────┘
```

**Step 3 — Talk the tradeoffs (this is what scores points):**
- **Incremental analysis** — only re-scan changed files/modules → huge latency + cost win. (Mirror: how you'd design any high-volume pipeline.)
- **Queue + autoscaling workers** — handle bursty commit load, isolate slow analyses.
- **Language-specific analyzers** — pluggable, independently deployable.
- **Multi-tenancy** — isolation for security/noisy-neighbor (Fortune 100 customers).
- **Caching** — AST/results cache for unchanged code.
- **Tradeoff:** latency vs cost vs false-positive rate — tune per customer.

**Step 4 — Director lens (your differentiator):**
- **Team structure:** platform squad (shared infra/queue/storage) + analyzer squads (per language) + a data/ML squad (finding ranking, false-positive reduction).
- **Metrics:** DORA (deploy freq, lead time, change-fail rate, MTTR) + product metrics (analysis latency, false-positive rate, findings acted-on).
- **Build vs buy:** reuse proven queue/storage; build the differentiated analysis core.

---

## 3.2 "Design the agentic verification + repair loop" (Foundation Agent)

```
┌──────────────┐
│  AI agent    │
│  proposes    │
│  code change │
└──────┬───────┘
       ▼
┌──────────────┐   ┌──────────────┐   ┌────────────────────┐
│  Verify      │──▶│  Findings    │──▶│  Decision:         │
│  (static +   │   │ (explainable,│   │  - clean → merge   │
│  context)    │   │  structured) │   │  - issues → repair │
└──────────────┘   └──────────────┘   └─────────┬──────────┘
       ▲                                         │
       │          ┌──────────────────┐           │
       └──────────│ Repair Agent     │◀──────────┘
        re-verify │ (fixes using     │  feed findings as context
                  │  findings + RAG  │
                  │  context)        │
                  └──────────────────┘
```

**Talk track:** "The repair agent consumes structured, explainable findings plus retrieved context, proposes a fix, then re-verifies — a closed loop until it passes the quality gate. The two hard problems: making findings *machine-actionable* (not just human-readable), and giving the repair agent enough *context* to fix correctly without breaking something else. That's why Context Augmentation matters. I've built this generate-verify-repair pattern for SQL; the principles transfer."

---

# PART 4 — Architecture Decision Framework (use when challenged)

When asked "why X over Y," answer in this structure:
1. **Requirement** — what the business/scale actually needs
2. **Options** — 2-3 real alternatives
3. **Tradeoff** — the axis that matters (latency/cost/consistency/complexity)
4. **Decision + why** — tied to the requirement
5. **What you'd revisit** — honest about limits

> Example: "Flink vs Spark Streaming at Lazada — needed true low-latency event-time processing at 100M events/day, not micro-batch. Flink won on latency and windowing; cost was the tradeoff, justified by the real-time SLA. If volume had been lower I'd have used Spark for ecosystem simplicity."

---

# Practice Checklist
- [ ] Sketch the **AC/DC verification loop** from memory (1.2)
- [ ] Sketch the **scalable analysis platform** + tradeoffs (3.1)
- [ ] Sketch your **Text-to-SQL guardrail loop** (2.3) — your strongest bridge story
- [ ] Sketch the **Makro Medallion Lakehouse** (2.1)
- [ ] Be ready to explain **Flink vs Spark**, **Lakehouse vs warehouse+lake**, **ClickHouse vs HBase**
- [ ] For every design, add the **Director lens**: team structure + metrics + build-vs-buy
- [ ] Always **clarify scale/constraints before drawing**
```
