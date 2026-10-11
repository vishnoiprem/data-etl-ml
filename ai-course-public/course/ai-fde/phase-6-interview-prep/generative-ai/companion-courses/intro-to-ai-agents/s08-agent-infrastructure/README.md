# Section 8: Agent infrastructure — the platform layer

> **Section 8 in one line:** the agent doesn't run in a vacuum; it runs on infrastructure. The 6 lectures in this section cover the 4 pillars of agent infrastructure: deployment platforms (Kubernetes, serverless, dedicated), observability (logs, metrics, traces), message brokers (queue, pub-sub, event bus), and the security perimeter. The FDE who can debug a 3am page across all 4 pillars is the FDE who can own a production agent.

## In 60 seconds

The 4-pillar infrastructure stack you must recite:

1. **Deployment** — Kubernetes (production), Lambda (bursty), VM (legacy). Stateless agent, stateful data.
2. **Observability** — logs + metrics + traces. OpenTelemetry. The 6-panel 3am dashboard: cost, latency, success rate, errors-by-category, queue depth, ceiling usage.
3. **Message broker** — synchronous (<50 concurrent), SQS (100-10K), Kafka (10K+ with replay), Redis Streams (existing Redis). The agent is a worker.
4. **Security** — 5 layers: API gateway, mTLS, secrets, audit log, identity. SOC 2 / HIPAA / PCI compliance maps.

The 3-level cost ceiling (recap): per-run, per-tenant per-day, per-process per-month. **If you only read one lecture, read L8-4** (the observability + 3am dashboard — the on-call survival kit).

## The 6 lectures in this section

| # | Lecture | Topic | Read time | Interview signal |
|---|---------|-------|-----------|-------------------|
| 1 | `L8-1-the-infrastructure-stack.md` | The 4 pillars: deployment, observability, message broker, security. The reference architecture. | 22 min | "What is the agent infra stack?" |
| 2 | `L8-2-deployment-platforms.md` | Kubernetes, serverless (Lambda, Cloud Run), dedicated VM. The 3 deployment patterns. | 24 min | "How do you deploy an agent?" |
| 3 | `L8-3-message-brokers-and-queues.md` | SQS, Kafka, Redis Streams, NATS. Async vs sync, fan-out, exactly-once. | 22 min | "How do you handle 1000 concurrent runs?" |
| 4 | `L8-4-observability-stack.md` | OpenTelemetry, Prometheus, Grafana, Datadog, Honeycomb. The 3 pillars of observability. | 24 min | "How do you debug a distributed agent?" |
| 5 | `L8-5-the-security-perimeter.md` | API gateway, mTLS, rate limiting, secrets management, audit logs. The trust boundary. | 22 min | "How do you secure an agent?" |
| 6 | `L8-6-cost-management-at-scale.md` | Per-tenant cost tracking, budget alerts, cost attribution, FinOps. The CFO conversation. | 22 min | "How do you manage cost at scale?" |

**Total: ~136 minutes of reading + hands-on.**

## Why this section exists

Sections 1-7 built the agent from first principles: the 7 ingredients, the 5 guardrails, the 4 testing layers, the 3 deployment patterns, the 4 observability metrics, the 4 error categories, the n8n platform. The agent is now a working piece of software. **But software doesn't run in a vacuum; it runs on infrastructure.** The FDE who can ship a working agent is the FDE who can land the engagement; the FDE who can ship + operate + debug a working agent is the FDE who can be on-call.

Section 8 is the platform layer. The 6 lectures cover the 4 pillars:

1. **Deployment.** Where does the agent run? Kubernetes, serverless, dedicated VM. The 3 patterns from L6.7 in production-grade detail.
2. **Observability.** How do you know the agent is healthy? Logs, metrics, traces. The 3 pillars of observability, beyond the L6.8 dashboard.
3. **Message broker.** How do you handle 1000s of concurrent runs? SQS, Kafka, Redis Streams. The async pattern, the fan-out pattern, the exactly-once pattern.
4. **Security.** How do you protect the agent? API gateway, mTLS, rate limiting, secrets management. The trust boundary, the audit log, the compliance layer.

The 5th pillar — cost management — is its own lecture because cost is the conversation the FDE has with the CFO. The FDE who can name the per-tenant cost, the per-day cost, the per-month cost, and the cost trend is the FDE who can defend the agent's budget to the CFO.

The 6th lecture — the integration of the 5 pillars into a single operational story — is the FDE's 3am playbook. The 5-step debugging playbook from L6.10 needs the 4 pillars to work: the audit log (observability), the trace (observability), the deployment platform (deployment), the message broker (resilience), the security perimeter (audit + compliance). Without the pillars, the playbook is incomplete.

## The case study that runs through this section

**Customer:** AtlasMart, a 50-person e-commerce company doing $50M/year. The agent handles 5,000 customer service requests/day: tracking, refunds, returns, exchanges, escalations. The agent is built on the 7 ingredients + 5 guardrails from Sections 2 + 6.

**Volume:** 5,000 requests/day = 200/hour = 3-4/second peak. p95 latency target: 2 seconds. Cost target: $200/month. SLA: 99.9% uptime.

**Why this case study:** it's the right scale for the infrastructure section. SMB (Section 7) is too small; enterprise (Section 9) is too large. AtlasMart is the "in-between" that most FDEs ship in the first 3 years. The infrastructure choices are real, the tradeoffs are real, the cost numbers are real.

## How to use this section

1. **Read L8-1 first** — the infrastructure stack overview. The 4 pillars + the 6 layers. Skip if you've shipped a production agent before.
2. **Read L8-2 to L8-5 in order** — each builds a pillar. The pillars are independent but the lectures build on each other.
3. **Read L8-6 last** — the cost management lecture. This is the CFO conversation, the most important non-technical lecture in the section.

**Hands-on:** each lecture has a "your turn" section with concrete exercises. Set up a free Kubernetes cluster (minikube, k3s, or a managed K8s from your cloud provider); deploy the PacificFreight agent; observe it with Prometheus + Grafana; rate-limit it with an API gateway.

## Read next

`L8-1-the-infrastructure-stack.md` — the 4 pillars + the 6 layers of agent infrastructure. The reference architecture that every FDE should be able to draw on a whiteboard in 5 minutes.
