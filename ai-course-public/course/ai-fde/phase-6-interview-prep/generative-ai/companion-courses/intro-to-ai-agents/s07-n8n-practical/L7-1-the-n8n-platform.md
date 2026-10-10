# L7.1: The n8n platform — workflows, nodes, executions

> **FDE framing in one line:** n8n is a node-based workflow editor where the canvas is the architecture. Every node is a function; every edge is a data flow; every execution is a run. The FDE who can read an n8n canvas like a circuit diagram is the FDE who can ship an SMB agent in a day instead of a sprint.

## The 3 things you'll learn

1. The 5 n8n primitives: workflow (the canvas), node (a function), credential (an API key), execution (a run), trigger (what starts the workflow). Each maps to a concept from Sections 2 + 6.
2. The data flow model: every node reads from its inputs, writes to its outputs, and the next node reads from the previous node's output. JSON is the lingua franca. The `$json`, `$node`, `$execution` variables are the FDE's API.
3. The "canvas as architecture" pattern: the visual layout is the documentation. The right canvas makes the agent's data flow obvious; the wrong canvas makes it opaque. **The FDE spends the first 5 minutes of every n8n session naming the nodes well.**

## Concept

n8n is a workflow automation platform with 1000+ pre-built integrations. The user builds "workflows" by dragging "nodes" onto a canvas, wiring them together, and configuring each node's behavior. When the workflow is triggered, n8n executes the nodes in order (or in parallel, depending on the wiring), passing JSON data between them. **Every n8n workflow is a visual program; every node is a function call; every edge is a parameter passing.**

The 5 n8n primitives:

1. **Workflow.** The canvas itself. A workflow is a directed graph of nodes + edges + a trigger. Workflows are saved in `~/.n8n/workflows/` (self-hosted) or in the n8n cloud. Each workflow has a unique ID, a name, a description, and a list of nodes. Workflows can be versioned, exported as JSON, and imported.
2. **Node.** A function. A node takes inputs (from previous nodes, from credentials, from user configuration), does work (call an API, transform data, run code), and produces outputs (JSON, binary, errors). Nodes are typed: trigger nodes start the workflow; regular nodes do work; output nodes send data somewhere. There are 1000+ pre-built nodes; users can write custom nodes in TypeScript.
3. **Credential.** A secret. A credential is a stored API key, OAuth token, or database connection string. Credentials are referenced by nodes (not embedded). The FDE never pastes an API key into a node's parameters; the FDE creates a credential once and references it. Credentials are encrypted at rest; access is controlled by user role.
4. **Execution.** A run. An execution is a single invocation of a workflow. Each execution has a unique ID, a start time, an end time, a status (success, error, waiting), and the JSON data at every node. Executions are stored for debugging; old executions can be deleted to save space. The "execution view" is the FDE's debugger.
5. **Trigger.** The entry point. A trigger is a special node that starts the workflow when something happens: a webhook receives an HTTP request, a schedule fires (cron), a new row appears in a database, an email arrives, a Slack message is posted. Every workflow has exactly one trigger (or a manual "execute" button).

The data flow model:

Every node reads from `{{$json}}` (the previous node's output), reads from `{{$node["NodeName"].json}}` (any earlier node's output), and writes to its own `{{$json}}` (the next node's input). The FDE builds a workflow by wiring nodes together; the data flows from left to right (or top to bottom, depending on the canvas orientation). **The JSON contract between nodes is the FDE's interface; the FDE reads the first execution's output to understand what each node produces.**

The 3 n8n variables the FDE uses constantly:

1. **`$json`** — the current node's input. The most common variable. Every node receives `$json` as its input data; the FDE references it in the node's parameters as `{{$json.field}}`.
2. **`$node["NodeName"].json`** — a specific earlier node's output. The FDE references it as `{{$node["HTTP Request"].json.id}}` to access the HTTP Request node's `id` field.
3. **`$execution`** — metadata about the current execution. `$execution.id` is the unique execution ID; `$execution.mode` is "test" or "production"; `$execution.resumeUrl` is the URL to resume a waiting execution (for HITL patterns).

The "canvas as architecture" pattern is the recognition that the visual layout of the workflow is the documentation. A well-built workflow is easy to read: trigger on the left, AI agent in the middle, outputs on the right. A poorly-built workflow is spaghetti: 30 nodes wired in a tangle, with no labels. **The FDE's first job is to make the canvas readable; the second job is to make the JSON contract clear.**

## The pattern

The 5 primitives in action (the simplest possible workflow):

```
[Webhook Trigger] → [Set Node] → [Slack Node]
```

- **Webhook Trigger:** receives an HTTP POST; the body becomes `$json`.
- **Set Node:** adds a field to `$json`; e.g., adds `timestamp: {{$now}}`.
- **Slack Node:** sends a message to a channel; uses the Set node's `$json.message` as the message text.

The execution log (what the FDE reads to debug):

```
[10:23:45] Webhook triggered: POST /webhook/lead
  Request body: {"email": "alice@example.com", "company": "Acme"}
[10:23:45] Set executed
  Output: {"email": "alice@example.com", "company": "Acme", "timestamp": "2026-10-10T10:23:45Z"}
[10:23:46] Slack executed
  Output: {"ok": true, "channel": "#leads", "ts": "1234567890.123456"}
[10:23:46] Workflow complete (1.2s)
```

The canvas (what the FDE sees):

```
┌─────────────┐     ┌──────────┐     ┌──────────┐
│  Webhook    │────▶│   Set    │────▶│  Slack   │
│  Trigger    │     │  Node    │     │  Node    │
└─────────────┘     └──────────┘     └──────────┘
```

The credentials (what the FDE configures once):

```yaml
credentials:
  slack_workspace:
    type: slack_oauth
    access_token: xoxb-***-***
    created_by: prem@customer.com
  openai_api:
    type: openai_api
    api_key: sk-***
    created_by: prem@customer.com
```

The n8n execution data (the JSON contract):

```json
{
  "executionId": "exec-abc123",
  "workflowId": "wf-lead-enrichment",
  "mode": "production",
  "startedAt": "2026-10-10T10:23:45.123Z",
  "finishedAt": "2026-10-10T10:23:46.345Z",
  "status": "success",
  "data": {
    "Webhook": {"email": "alice@example.com", "company": "Acme"},
    "Set": {"email": "alice@example.com", "company": "Acme", "timestamp": "2026-10-10T10:23:45Z"},
    "Slack": {"ok": true, "channel": "#leads", "ts": "1234567890.123456"}
  }
}
```

The pattern that wins interviews is the "5 primitives + JSON contract + canvas as architecture" pattern. The candidate who says "n8n has 5 primitives: workflow (the canvas), node (a function), credential (a secret), execution (a run), trigger (the entry point). The JSON contract is the interface between nodes; `$json`, `$node`, `$execution` are the variables. The canvas is the documentation; I spend the first 5 minutes naming nodes well. The wrong choice is to build a spaghetti workflow with 30 unlabeled nodes. The right choice is to make the canvas readable + the JSON contract explicit" is the candidate who demonstrates the n8n-mindset.

## Code or example

The 4-axis rubric for picking n8n (when to use it vs not):

```python
def should_use_n8n(requirements: dict) -> bool:
    """Pick n8n when the team is not engineering-first."""
    return all([
        requirements.get("team_is_engineering_first", False) is False,
        requirements.get("latency_p95_s", 5.0) > 1.0,  # n8n is not for sub-second
        requirements.get("concurrent_runs", 100) < 100,  # n8n is not for 1000s
        requirements.get("integrations_count", 5) >= 3,  # n8n shines at 3+ integrations
    ])

# Example: Northwind Logistics (8-person SMB, 200 leads/day)
# - Team: not engineering-first (1 engineer, 5 ops, 2 sales)
# - Latency: 5 minutes (not 1 second)
# - Concurrent: 5 (not 100s)
# - Integrations: 6 (Slack, HubSpot, Clearbit, LinkedIn, Postgres, email)
# Verdict: n8n is the right tool
```

The n8n CLI commands the FDE uses daily:

```bash
# Install n8n locally
npm install n8n -g
# or
npx n8n

# Start n8n (default port 5678)
npx n8n start
# or
npx n8n start --tunnel  # for testing webhooks from external services

# List all workflows
curl -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows

# Execute a workflow via API
curl -X POST http://localhost:5678/api/v1/workflows/wf-123/execute \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "company": "Acme"}'

# Export a workflow as JSON
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  http://localhost:5678/api/v1/workflows/wf-123 | jq '.nodes' > workflow.json

# Import a workflow from JSON
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @workflow.json
```

The n8n workflow export (the FDE's source of truth):

```json
{
  "name": "Lead Enrichment",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "lead",
        "responseMode": "onReceived"
      }
    },
    {
      "name": "Set",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {"name": "timestamp", "value": "={{$now}}"},
            {"name": "source", "value": "webhook"}
          ]
        }
      }
    },
    {
      "name": "Slack",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [650, 300],
      "parameters": {
        "channel": "#leads",
        "text": "={{$json.email}} from {{$json.company}}"
      },
      "credentials": {"slackApi": {"id": "cred-1", "name": "slack_workspace"}}
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "Set", "type": "main", "index": 0}]]},
    "Set": {"main": [[{"node": "Slack", "type": "main", "index": 0}]]}
  }
}
```

## Production addendum

The n8n platform question is the answer to "what is n8n and when do you use it." The 60-second script:

> "5 primitives. Workflow (the canvas), node (a function), credential (a secret), execution (a run), trigger (the entry point). Every node reads `$json` and writes `$json`; the FDE references earlier nodes via `$node["NodeName"].json`. The canvas is the documentation; I spend 5 minutes naming nodes well. The wrong choice is to build spaghetti workflows with unlabeled nodes. The right choice is the 5 primitives + the JSON contract + the canvas as architecture. n8n is the right tool for non-engineering teams; the wrong tool for sub-second latency or 1000s of concurrent runs."

This is the difference between a candidate who says "I used n8n" and a candidate who says "5 primitives, JSON contract, canvas as architecture, 4-axis rubric for when to use it vs code." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/n8n/` — the n8n workflow examples.
- **Reference implementation**: `course/hardcode/level-7-n8n/` — the n8n reference patterns.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — n8n as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/04-ai-data-analyst/` — the data analyst agent could be built in n8n (sandbox node).
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — n8n as a system design choice.

## The 3 questions this lecture preps you for

1. **"What is n8n and when do you use it?"** Answer: n8n is a visual workflow automation platform with 5 primitives (workflow, node, credential, execution, trigger). The right tool for non-engineering teams, integrations-heavy workflows, latency-tolerant automations. The wrong tool for sub-second latency or 1000s of concurrent runs.
2. **"How do you debug an n8n workflow?"** Answer: the execution view shows every node's input + output JSON; the FDE reads the failed node's input to see what was passed; reads the failed node's output to see what was produced; reads the next node's input to see what it received. The execution log is the timeline; `$json` is the current state.
3. **"What is the canvas as architecture pattern?"** Answer: the visual layout of the workflow is the documentation. The FDE spends the first 5 minutes naming nodes well; positions nodes left-to-right (trigger → processing → output); uses consistent colors for similar node types. The wrong choice is spaghetti workflows with 30 unlabeled nodes. The right choice is the readable canvas + the explicit JSON contract.

## Read next

`L7-2-your-first-workflow.md` — the first workflow: Webhook → HTTP Request → Slack in 10 minutes. The "hello world" that proves the FDE pattern in n8n.
