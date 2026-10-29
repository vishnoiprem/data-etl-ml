# Step 1 — Clarify (the 5 questions you ask before drawing)

> **The clarifying step is the FDE signal.** Most candidates skip it. Senior FDEs spend 5-7 minutes here because the questions reveal the customer, the constraint, the failure mode. The technology is downstream of the constraint. **Clarify first, design second.**

---

## The 5 questions (always, in this order)

### 1. "Who is the user?"

This is the customer question. The answer drives every design decision downstream.

| User | Design implication |
|---|---|
| Internal CS team (Mei at PacificFreight) | Latency < 2s; cost ceiling per user; thumbs-up metric |
| End customer (the email sender) | Latency < 500ms; no cost ceiling per user; CSAT metric |
| Ops team (Sarah) | Read-heavy; aggregation; daily/weekly reports |
| IT team (Daniel) | Observability; cost dashboard; on-call rotation |
| External partner (carrier API) | Webhook reliability; retry policy; rate-limit handling |

**The FDE signal:** when the candidate says "who is the user?" they're showing they understand the system serves a person, not a technology.

### 2. "What's the scale?"

This is the QPS question. The answer drives the architecture (single-VM vs multi-region, monolith vs microservices, in-process state vs Redis).

| Scale | Architecture |
|---|---|
| < 100 QPS | Single VM, monolith, in-process state, no Redis |
| 100-10k QPS | Multi-worker, Redis for state, single region |
| 10k-100k QPS | Multi-region, Redis cluster, read replicas |
| > 100k QPS | Microservices, K8s, multi-region, custom routing |

**The FDE signal:** when the candidate says "10k QPS" AND "1 tenant" they're showing they understand the operational boundary. Different scale → different cost.

### 3. "What's the constraint?"

This is the cost / latency / compliance question. The answer drives the design decisions (which LLM, which DB, which rate limit).

| Constraint | Design implication |
|---|---|
| Cost ceiling $5/month | Use SLM (Qwen 1.5B), in-process for MVP, single region |
| Latency < 500ms | Use streaming, pre-warm connections, edge cache |
| HIPAA compliance | Per-record encryption, audit log, no LLM with PII |
| 99.95% SLA | Multi-region DR, circuit breaker, on-call rotation |
| GDPR (data residency) | Single region in EU, no cross-border replication |

**The FDE signal:** when the candidate says "the cost ceiling is $5/month" AND "we can use an SLM at 0.5% of the cost" they're showing they understand the operational boundary AND the technology tradeoffs.

### 4. "What's the failure mode?"

This is the resilience question. The answer drives the circuit breaker, the fallback, the on-call rotation.

| Failure mode | Design implication |
|---|---|
| LLM hallucinates a wrong shipment status | Citation in every draft; redactor on outbound; thumbs-down feedback loop |
| LLM API is down | Fallback to templated draft; circuit breaker at 5 errors/min |
| Database is down | Read replica; queue writes; alert on-call |
| Region is down | Multi-region DR; DNS failover; S3 sync |
| Cost ceiling breached | Manual throttle; auto-pause non-critical features; on-call page |

**The FDE signal:** when the candidate names the worst-case failure mode AND the mitigation, they're showing they understand operational reality.

### 5. "What's the timeline?"

This is the MVP question. The answer drives the phasing (what ships in week 1, week 4, week 12).

| Timeline | Phase 1 (week 1-2) | Phase 2 (week 3-6) | Phase 3 (week 7-12) |
|---|---|---|---|
| 2 weeks | Single-VM, mock data, no eval set | (post-MVP) | (post-MVP) |
| 2 months | Single-VM, eval set, cost ceiling, on-call | Multi-worker, Redis, OAuth | Multi-region, SLM |
| 6 months | All of 2 months + MCP + multi-agent | All of 2 months + gVisor + multi-region | Continuous iteration |

**The FDE signal:** when the candidate says "MVP in 2 weeks, production in 2 months" they're showing they understand the difference between a demo and a system that survives the customer.

---

## The 5 anti-patterns (clarifying-step mistakes)

1. **Asking only technical questions.** "What's the QPS?" is technical. "Who is the user?" is customer. The FDE signal is the customer question.
2. **Asking closed-ended questions.** "Is the cost ceiling $5?" is closed. "What's the cost ceiling and how was it decided?" is open.
3. **Asking 10 questions.** 5 is the signal. 10 is the symptom of not thinking.
4. **Skipping the clarifying step entirely.** The candidate who starts drawing before asking is signaling "I optimize for the wrong thing."
5. **Asking questions the interviewer can't answer.** "What's the budget?" is fine. "What does the CEO think?" is unanswerable.

---

## The 3 clarifying-question bank (saved questions that work)

When the interviewer pushes back ("just start drawing"), use one of these:

1. **"I want to make sure I'm solving the right problem. Can I ask 2-3 more questions before I start?"** (The polite version of "I'm not skipping this step.")
2. **"Let me write down 5 questions and ask them in parallel. Then I'll start."** (The efficient version.)
3. **"If I have to pick one constraint to optimize for, which is it — cost, latency, or accuracy?"** (The fallback when the interviewer cuts you off.)

---

## How to use this file

1. **Memorize the 5 questions.** They're the same for every decomposition round.
2. **Practice on the 5 sample questions in `../README.md`.** Time yourself: 5-7 minutes for the 5 questions.
3. **Rehearse out loud.** The clarifying step is performance; the AI assistant can score you on whether you skipped it.
4. **Use the 3 fallback questions when the interviewer pushes back.** "Just start drawing" is a test; the fallback is the right response.
