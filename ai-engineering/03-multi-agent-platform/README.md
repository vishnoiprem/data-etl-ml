# 03 — Multi-Agent Platform on Bedrock AgentCore

> **Customer problem:** Replace a 47-step manual loan-origination workflow (document intake → KYC/AML → credit analysis → policy checks → exception routing) with an agentic system. Goal: 60%+ straight-through automation, decision time from 6 days to 4 hours.

This project shows the **theory and skeleton of agentic AI**: tool use, ReAct-style reasoning, multi-agent orchestration, memory, and human-in-the-loop. It runs offline with deterministic stub agents so you can see the orchestration shape, with Bedrock AgentCore as the production target.

---

## 1. Theory: What is an "agent" in 2026?

An LLM agent is a loop:

```
while not done:
    obs = environment_state()
    thought, action = LLM(prompt + history + tools)
    result = execute(action)        # call a tool, MCP server, API
    history.append((thought, action, result))
```

Three things make this work:
- **Tool use** — structured function calls (JSON), not free text.
- **Reasoning trace** — the model thinks before acting (ReAct, plan-and-execute, reflexion).
- **Memory** — short-term (the loop's history) and long-term (vector store + structured store).

## 2. Single agent vs. multi-agent

| Pattern | When | Why |
|---|---|---|
| Single agent + many tools | Most cases | Simpler to debug, cheaper, fewer coordination failures |
| Hierarchical (orchestrator + specialists) | Workflows that decompose cleanly into specialized tasks | Each specialist has a smaller prompt + tool set → better quality |
| Swarm / debate | Research, brainstorming | Diversity of approaches; rarely needed in enterprise |

For loan origination we use **hierarchical**: an orchestrator routes to KYC, Credit, and Policy specialists. Each specialist owns ~5 tools and its own scratchpad.

## 3. Bedrock AgentCore primitives

- **Runtime** — managed loop with built-in tool-use, memory, and tracing.
- **Memory** — short-term (session) and long-term (semantic) memory APIs.
- **Identity** — IAM-bound agent identity for tool calls.
- **Code Interpreter** — sandboxed Python execution.
- **Browser** — headless web browsing as a tool.
- **Gateway** — turns OpenAPI specs / MCP servers into agent tools with auth.
- **Observability** — every loop iteration is a span; failures, loops, and cost are visible.

## 4. Failure modes catalog

Real agent systems fail in predictable ways. We track 15 categories with mitigations:

| # | Mode | Mitigation |
|---|---|---|
| 1 | Infinite loop | Step budget + loop detector (hash repeat) |
| 2 | Tool-call schema error | JSON-schema validation, retry with error feedback |
| 3 | Hallucinated tool name | Whitelist tools, refuse + correct |
| 4 | Wrong tool for task | Few-shot tool descriptions, eval suite |
| 5 | Stale memory | TTL on memory entries, freshness-on-read |
| 6 | Context bloat | Summarize history > N steps |
| 7 | Privilege escalation | IAM-scoped tool roles |
| 8 | Prompt injection from tool result | Sanitize tool outputs, treat as untrusted |
| 9 | Cost runaway | Per-task budget, kill-switch |
| 10 | Indecision (asks user too much) | Clarification budget |
| 11 | Premature termination | Goal-completion check |
| 12 | Specialist deadlock | Circuit breaker, escalate to human |
| 13 | Numerical errors | Use code-interpreter for math |
| 14 | Stale data | Cache TTL, freshness signal in tool response |
| 15 | Unhandled exception | Error envelope, retry then escalate |

## 5. Architecture

```
                                    ┌──────────────────────────┐
   user / API ──────────────────────▶│      Orchestrator        │
                                    │  (Bedrock AgentCore)     │
                                    └─────────┬────────────────┘
                                              │ delegate
                  ┌───────────────────────────┼───────────────────────────┐
                  ▼                           ▼                           ▼
         ┌────────────────┐          ┌────────────────┐          ┌────────────────┐
         │  KYC Agent     │          │ Credit Agent   │          │ Policy Agent   │
         │  - id_verify   │          │ - bureau_pull  │          │ - rule_engine  │
         │  - sanctions   │          │ - dti_calc     │          │ - jurisdiction │
         │  - pep_check   │          │ - income_verify│          │ - exception    │
         └────────────────┘          └────────────────┘          └────────────────┘
                  │                           │                           │
                  ▼                           ▼                           ▼
         ┌────────────────────────────────────────────────────────────────────────┐
         │               Tools layer (Lambda action groups + MCP)                  │
         │   AcmeKYC, ExperianAPI, CoreBanking, RuleEngine, OFAC                  │
         └────────────────────────────────────────────────────────────────────────┘

   Memory:  AgentCore Memory (short)  +  DynamoDB+OpenSearch (long-term)
   HITL:    Step Functions for >$250K decisions
   Audit:   Every step logged to S3 + CloudTrail
```

## 6. Project Layout

```
03-multi-agent-platform/
├── README.md
├── Makefile
├── requirements.txt
├── src/
│   ├── tools.py           Stub tool implementations (KYC, credit, policy)
│   ├── memory.py          Short/long-term memory abstraction
│   ├── agent.py           Single-agent ReAct loop with tool use
│   ├── orchestrator.py    Hierarchical multi-agent orchestrator
│   └── policies.py        Routing policies + budget/loop guards
├── sample_data/
│   └── applications.jsonl 5 sample loan applications
├── scripts/
│   ├── run_application.py CLI: run one application end-to-end
│   └── run_batch.py       CLI: run all applications + summary
└── tests/
```

## 7. Quick Start

```bash
pip install -r requirements.txt
make demo
```

Runs all 5 sample applications through the orchestrator and prints the
decision (approve / decline / refer-to-human) plus the full trace.

## 8. Production Path

`scripts/bedrock_agentcore_deploy.py` shows the production deploy:
1. Define each specialist as a Bedrock Agent (or AgentCore agent).
2. Wire tools as Lambda action groups; for SaaS APIs, wrap in a Gateway with OAuth.
3. Configure memory: AgentCore Memory for sessions, DynamoDB for KYC history.
4. Add Bedrock Guardrails for PII redaction in tool outputs.
5. Enable AgentCore Observability; pipe traces to CloudWatch + X-Ray.
6. Step Functions for HITL gates (>$250K decisions).

## 9. What "Done" Looks Like

| Metric | Target |
|---|---|
| Straight-through rate | ≥ 60% |
| Time-to-decision (STP) | ≤ 4 hours |
| Agent task success | ≥ 90% |
| Cost / decision | < $0.50 |
| Human-review accuracy on sampled decisions | ≥ 98% |
