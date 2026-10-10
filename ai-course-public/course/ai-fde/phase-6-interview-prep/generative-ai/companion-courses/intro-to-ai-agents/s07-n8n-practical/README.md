# Section 7: Practical example — Build an agentic automation with n8n

> **Section 7 in one line:** n8n is the FDE's low-code agentic platform. The 7 ingredients + the 5 guardrails from Sections 2 + 6 apply; the implementation is visual instead of code. The candidate who can ship a non-engineering team's first agent in n8n is the candidate who can land the SMB engagement.

## In 60 seconds

The 5 named primitives of n8n you must recite:

1. **Workflow** — a DAG of nodes; the artifact you ship.
2. **Node** — a single step (trigger, data, action, logic).
3. **Credential** — the API key / OAuth / DB cred (stored in n8n's vault, never in code).
4. **Execution** — one run of a workflow; logged for replay + debugging.
5. **Trigger** — webhook, schedule, or event that starts the workflow.

The 4-axis rubric for "n8n vs code": **team capability, customization, time-to-first-workflow, lock-in.** n8n wins for non-engineers, <2-week time-to-value, simple integrations. Code wins for 5+ tools, custom eval, complex reasoning. **If you only read one lecture, read L7-7** (the 6-node complete automation — the end-to-end artifact).

## The 8 lectures in this section

| # | Lecture | Topic | Read time | Interview signal |
|---|---------|-------|-----------|-------------------|
| 1 | `L7-1-the-n8n-platform.md` | n8n architecture: workflows, nodes, credentials, executions | 21 min | "Why n8n vs LangGraph?" |
| 2 | `L7-2-your-first-workflow.md` | Hello world: trigger → HTTP → Slack in 10 minutes | 18 min | Walk through a basic flow |
| 3 | `L7-3-nodes-and-credentials.md` | 1000+ nodes, OAuth/API key setup, the credential redaction pattern | 22 min | "How do you handle 100s of integrations?" |
| 4 | `L7-4-the-ai-agent-node.md` | The AI Agent node: model + system prompt + tools + memory | 24 min | "How does n8n implement the 7 ingredients?" |
| 5 | `L7-5-vector-store-and-memory.md` | Qdrant / Pinecone / Postgres pgvector; simple vs window memory | 20 min | "How do you add RAG to an n8n workflow?" |
| 6 | `L7-6-error-handling-in-n8n.md` | Error workflow, retry, continue-on-fail, IF/Switch nodes | 22 min | "How do you make n8n production-ready?" |
| 7 | `L7-7-building-a-complete-automation.md` | End-to-end: lead capture → enrich → qualify → CRM → Slack | 28 min | Live demo the FDE pattern |
| 8 | `L7-8-when-to-use-n8n-vs-code.md` | The 4-axis rubric: team, scale, latency, cost | 20 min | "n8n vs LangGraph vs raw Python?" |

**Total: ~175 minutes of reading + hands-on.**

## Why this section exists

Sections 1-6 built the agent from first principles: 200 lines of stdlib Python, the 7 ingredients, the 5 guardrails, the 4 testing layers. That's the right foundation for engineers — but most of the FDE's customers are not engineers. The SMB customer has 2 engineers, 5 ops people, and a CFO. They don't write Python; they configure tools. n8n is the platform that lets them do that.

n8n is a visual workflow editor with 1000+ pre-built nodes for common services (Slack, Salesforce, HubSpot, Postgres, OpenAI, Anthropic, Google Sheets, Notion, etc.). The user drags nodes onto a canvas, wires them together, configures credentials, and ships a workflow in hours instead of weeks. **n8n is the right tool when the customer is not engineering-first; it's the wrong tool when they need sub-second latency or 1000s of concurrent runs.**

The lectures in this section teach the FDE pattern as expressed in n8n. The 7 ingredients map to n8n primitives:

| Ingredient (Section 2) | n8n primitive |
|---|---|
| Model | AI Agent node → model selector (OpenAI, Anthropic, Ollama) |
| Tools | Tool nodes (HTTP Request, Postgres, Slack, custom function) |
| Memory | Window Buffer Memory, Postgres Chat Memory, Vector Store nodes |
| Cost ceiling | Per-node execution limits + workflow timeout + the "Max iterations" field |
| System prompt | The "System Message" field on the AI Agent node |
| Parser | Implicit (n8n parses model output into the next node's input) |
| Loop driver | The AI Agent node's loop; max iterations = 30 by default |

The 5 guardrails from Section 6.5 map to n8n patterns:

| Guardrail (Section 6.5) | n8n pattern |
|---|---|
| Loop detector | The "Max iterations" field on the AI Agent node |
| Schema validator | The "Output Parser" node (auto-fixing output to a JSON schema) |
| Cost ceiling | Workflow execution timeout + per-node limits |
| Idempotency | The "Idempotency Key" field on the AI Agent node |
| Audit log | The "Execution" view + the `n8n` audit log API |

The pattern that wins interviews is the "n8n implements the same 7 + 5 pattern" pattern. The candidate who says "I built the same agent in both Python (200 lines) and n8n (a visual workflow with 6 nodes). The 7 ingredients + 5 guardrails are the contract; the implementation is either code or visual. The right choice is n8n for non-engineering teams, code for sub-second latency or 1000s of concurrent runs" is the candidate who demonstrates the platform-mindset.

## The case study that runs through this section

**Customer:** Northwind Logistics, an 8-person cross-border freight broker. They take 200 lead emails/day from prospective customers. Today, a human reads each one, looks up the company on LinkedIn, checks if the lane (Singapore ↔ Vietnam) is supported, and routes qualified leads to a sales rep.

**Goal:** automate the lead qualification. The agent reads the email, enriches with LinkedIn + Clearbit, checks lane coverage, scores the lead, and writes to HubSpot + Slack.

**The build:** Section 7 walks through the n8n workflow that does this end-to-end. The first 6 lectures build the building blocks; L7-7 assembles them.

**Why this case study:** it's a real SMB engagement. The CTO is willing to spend 1 day configuring n8n; he is not willing to spend 2 weeks writing Python. n8n is the right tool. The agent saves 3 hours/day of human triage; the cost is $0.30/day in LLM API calls.

## How to use this section

1. **Read L7-1 first** — the n8n platform overview. Skip if you've used n8n before.
2. **Read L7-2 to L7-6 in order** — each builds a primitive the next one uses.
3. **Read L7-7 carefully** — this is the full build. Treat it as the synthesis.
4. **Read L7-8 last** — the platform decision rubric. This is the interview-prep finale.

**Hands-on:** each lecture has a "your turn" section at the end. Spin up a free n8n cloud account (https://n8n.io) or run n8n locally via `npx n8n` and follow along. The Northwind case study builds an end-to-end workflow in 8 lectures.

## Read next

`L7-1-the-n8n-platform.md` — the n8n platform architecture. Workflows, nodes, credentials, executions, and the data flow that connects them.
