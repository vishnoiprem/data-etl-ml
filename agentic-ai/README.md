# Agentic AI — 19 Production Agents, MCP, Tool-Use, Multi-Agent Debate, MLOps fine-tune

> **Nineteen working agent systems across MCP, browser-use, IDE-style,
> hiring, customer service, debate, computer-use, and MLOps fine-tuning.** LangGraph ·
> Anthropic · OpenAI · Bedrock · MCP · RAGAS · DeepEval · MLflow · vLLM · Prometheus.

This directory is the agentic-AI half of the portfolio. The bar I set for
myself: every project ships an eval harness, a cost-per-task number, and a
bounded-loop guarantee. If an agent can't tell you its p50 cost, its p95
latency, and its p99 failure mode, it's a demo, not a product.

---

## What's in this directory

### MCP / Tool-use primitives

| # | Project | What it is | Why it's here |
|---|---------|------------|---------------|
| 1 | [**1-wikipedia_mcp_assistant**](./1-wikipedia_mcp_assistant/) | The smallest correct MCP project. Tools, prompts, resources, LangGraph client | The "show me what MCP actually does" reference |
| 2 | [**6_wiki_rag_react_project**](./6_wiki_rag_react_project/) | ReAct loop over Wikipedia via MCP, with eval on faithfulness | ReAct reference |
| 3 | [**4-AI-Agents-MCP**](./4-AI-Agents-MCP/) | A multi-server MCP setup, the way you'd structure a real production agent | Multi-server MCP |

### Bedrock / AWS-native

| # | Project | What it is | Why it's here |
|---|---------|------------|---------------|
| 4 | [**3-aws-bedrock-aurora-s3**](./3-aws-bedrock-aurora-s3/) | Bedrock agent over Aurora + S3, end-to-end | AWS-native agent reference |
| 5 | [**5-amazon-transcribe**](./5-amazon-transcribe/) | Audio-in / structured-data-out agent pipeline | Multi-modal |
| 6 | [**7_Bedrock_course**](./7_Bedrock_course/) | 6-module Bedrock agent curriculum | Teaching reference |
| 7 | [**2-enterprise-search-agent-full**](./2-enterprise-search-agent-full/) | Full enterprise search agent, hybrid retrieval, permission-aware | Production reference |

### Agentic systems (the meat)

| # | Project | What it is | Why it's here |
|---|---------|------------|---------------|
| 8 | [**10-ide-agent-cursor-style**](./10-ide-agent-cursor-style/) | Cursor-style inline edit agent, with diff-aware retrieval | IDE agent reference |
| 9 | [**11-general-agent-manus-style**](./11-general-agent-manus-style/) | General-purpose computer-use agent in the Manus style | Long-horizon planning |
| 10 | [**13-browser-agent-comet-style**](./13-browser-agent-comet-style/) | Comet-style browser agent, human-in-the-loop safety | Browser-use reference |
| 11 | [**14-hiring-agent**](./14-hiring-agent/) | Hiring pipeline: job description → candidate shortlist → outreach drafts | Domain-specific agent |
| 12 | [**15-multi-agent-debate**](./15-multi-agent-debate/) | Two debaters, one verifier. Used for high-stakes decisions | Multi-agent with verifier |
| 13 | [**16-autonomous-loop**](./16-autonomous-loop/) | Autonomous long-running agent with budget + retry + write-ahead log | The pattern every real agent ends up needing |
| 14 | [**17-computer-use-agent**](./17-computer-use-agent/) | Screenshot → action loop, screen + DOM, with retry + guardrails | Computer-use |
| 15 | [**8-swe-agent-devin-style**](./8-swe-agent-devin-style/) | Devin-style SWE agent: read repo, plan, edit, run tests, PR | SWE agent |
| 16 | [**9-terminal-agent-claude-code**](./9-terminal-agent-claude-code/) | Claude-Code-style terminal agent, sandboxed, bash + file edit | Terminal agent |
| 17 | [**12-customer-service-agent**](./12-customer-service-agent/) | Customer service agent with policy lookup, escalation, post-mortem | Production domain agent |
| 18 | [**agent_deployment_databricks**](./agent_deployment_databricks/) | Same agent surface, but on Databricks model serving with Lakehouse monitoring | Deployment story |
| 19 | [**19-mlops-finetune-genai**](./19-mlops-finetune-genai/) | End-to-end MLOps: QLoRA SFT on Llama 3.1 8B, MLflow register, vLLM serve, Prometheus + Evidently drift | ML-Ops + serving |

---

## Design philosophy

Four rules I hold every project in this directory to. Same four rules the
`data-engineering/` directory holds, but spelled out for agents:

### 1. Bounded loops

Every agent has a max-step count, a max-cost budget, and a max-wall-clock.
If any of those trips, the agent returns a structured failure (not a stack
trace). The `16-autonomous-loop/` project is the reference implementation
of this rule.

### 2. Eval is in the loop, not after

Every agent has an eval harness that runs on every PR. Eval scores are
tracked over time. If a change drops the eval score by > X%, CI fails.
The eval is RAGAS / DeepEval / a custom domain metric — whatever fits.
The point is the gate, not the library.

### 3. Cost-per-task is a feature

Every agent has a cost column in its README: p50, p95, p99 cost per task,
per 1k tasks, per 10k tasks. The cost includes model tokens, tool calls,
retry overhead, and human-in-the-loop minutes. If the cost model is
hand-wavy, the README isn't done.

### 4. Verification, not vibes

Multi-agent systems get a verifier or a critic. Single-agent systems get
a self-check or a constraint check. The point is to make the agent's
output provable rather than plausible. `15-multi-agent-debate/` is the
canonical example.

---

## How the pieces compose

The five patterns every production agent needs — and where they live here:

| Pattern | Where |
|--------|-------|
| **Tool use / MCP** | `1-wikipedia_mcp_assistant/`, `4-AI-Agents-MCP/` |
| **Retrieval (RAG over the agent's domain)** | `2-enterprise-search-agent-full/`, `6_wiki_rag_react_project/` |
| **Bounded loop / budget / retry** | `16-autonomous-loop/` |
| **Verifier / critic** | `15-multi-agent-debate/` |
| **Post-mortem / observability** | `12-customer-service-agent/`, `agent_deployment_databricks/` |
| **Fine-tune → serve → drift** | `19-mlops-finetune-genai/` |

A real production agent uses all of these. The projects here are decomposed so
each one has a clear focus; in production, you'd compose them.

---

## What this directory is NOT

- **Not a 100-eval library.** I picked the metrics that actually matter
  per project (faithfulness for RAG, task-completion + p95 cost for
  agents, refusal-fidelity for multi-agent debate). I didn't pad the
  eval count.
- **Not a LangChain showcase.** I use LangGraph where it's the right
  choice, plain Python + OpenAI/Anthropic where it isn't.
- **Not production-deployed-as-is.** These are reference builds. The
  reference patterns ship; the secrets, the rate limits, the tenant
  auth — those are tuned per-deployment.

---

## How to navigate

- **Show me MCP in 20 minutes:** start at `1-wikipedia_mcp_assistant/`.
- **Show me a production agent for a domain:** `12-customer-service-agent/`
  or `14-hiring-agent/`.
- **Show me multi-agent safety:** `15-multi-agent-debate/`.
- **Show me cost / budget discipline:** `16-autonomous-loop/`.
- **Show me AWS-native:** `3-aws-bedrock-aurora-s3/`.
- **Show me the curriculum angle:** `7_Bedrock_course/`.
- **Show me ML-Ops end to end:** `19-mlops-finetune-genai/` — QLoRA fine-tune,
  MLflow register, vLLM serve, Prometheus + drift alerting.

---

## Related directories

- [`../ai-engineering/`](../ai-engineering/) — 40 production LLM projects
  (the model + eval + ops half). Sibling to this one.
- [`../data-engineering/`](../data-engineering/) — The 18 data-platform
  projects. Agents need data platforms; the data platforms here are what
  the agents reason over.
- [`../leads-pipeline/`](../leads-pipeline/) — The hiring-agent and
  customer-service-agent patterns are the same patterns I use to ship
  real outreach. Concrete, not aspirational.
