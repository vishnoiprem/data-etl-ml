# L7.6: Error handling in n8n — the error workflow, retry, and the IF/Switch pattern

> **FDE framing in one line:** n8n error handling is the same 4-category taxonomy from Section 6.9 — transient, permanent, model, tool — expressed as 4 n8n primitives: error workflow, retry, continue-on-fail, and IF/Switch. The FDE's job is to map the error category to the right n8n primitive. The wrong choice is to ignore errors; the right choice is the 4 categories × 4 primitives matrix.

## The 3 things you'll learn

1. The 4 n8n error primitives: error workflow (catch-all for any failure), retry on error (per-node retry with backoff), continue-on-fail (per-node graceful degradation), IF/Switch (branch on error category). The matrix of (4 error categories × 4 primitives) is the FDE's error-handling toolkit.
2. The 3 retry patterns: per-node retry (built into every node), workflow-level retry (re-run the entire workflow), custom retry (Code node with custom logic). The FDE picks the right retry pattern for the right error.
3. The "error workflow as the 3am alert" pattern: every production workflow has an error workflow that fires when any node fails. The error workflow sends a Slack alert with the execution ID, the failed node, the error message, and the input data. The on-call reads the alert, opens the execution, and triages.

## Concept

n8n error handling is the same 4-category taxonomy from Section 6.9 — transient, permanent, model, tool — but expressed as 4 n8n primitives: error workflow, retry, continue-on-fail, and IF/Switch. The FDE's job is to map the error category to the right n8n primitive. **The 4 × 4 matrix is the FDE's error-handling toolkit; the wrong choice is to ignore errors; the right choice is the matrix.**

The 4 n8n error primitives:

1. **Error workflow.** A separate workflow that fires when any node in the main workflow fails. The error workflow receives the failed execution's data (execution ID, failed node, error message, input data). The FDE creates one error workflow per project; the error workflow sends a Slack alert to `#oncall`. Every production workflow has an error workflow.
2. **Retry on error.** A per-node setting that retries the node on failure. The FDE configures: max retries (default 3), retry interval (default 1000ms), backoff multiplier (default 2). The retry is the right primitive for transient errors (network timeout, 429 rate limit).
3. **Continue-on-fail.** A per-node setting that continues the workflow even if the node fails. The FDE configures: on error, return a default value (e.g., `{"ok": false, "error": "..."}`). The continue-on-fail is the right primitive for non-critical steps (e.g., enrichment that's nice-to-have but not required).
4. **IF/Switch.** A node that branches on a condition. The FDE uses IF to check the error object (`{{$json.error}}` is truthy → branch to error handling). The IF/Switch is the right primitive for permanent errors (404 not found → escalate to human).

The 3 retry patterns:

1. **Per-node retry.** Built into every node. The FDE configures max retries + backoff. The right pattern for transient errors on a single node (HTTP timeout, Postgres deadlock).
2. **Workflow-level retry.** The FDE wraps the entire workflow in a "Retry" workflow that re-runs on failure. The right pattern for transient errors that affect the whole workflow (e.g., database connection lost at the start).
3. **Custom retry.** A Code node that implements custom retry logic. The right pattern for complex retry conditions (e.g., retry only if the error message contains "rate limit"; use exponential backoff; give up after 3 tries).

The "error workflow as the 3am alert" pattern is the recognition that every production workflow needs an error workflow. The error workflow is a separate n8n workflow that:

1. Trigger: Error Trigger (fires when any node in the target workflow fails)
2. Data: receives the failed execution's data (execution ID, failed node, error message, input data)
3. Action: sends a Slack alert to `#oncall` with: execution ID, failed node, error message, input data (truncated to 1KB), workflow name
4. Action: writes to a Postgres table for the audit log
5. Action: opens a PagerDuty incident if the error category is "critical"

**The error workflow is the FDE's 3am alert; the on-call reads the alert, opens the execution, and triages.** The error workflow is not optional; it is the production-readiness contract.

## The pattern

The 4 × 4 matrix (the FDE's error-handling toolkit):

```python
ERROR_MATRIX = {
    "transient": {
        "description": "Network timeout, 429 rate limit, 503 service unavailable, database deadlock",
        "n8n_primitive": "Retry on error",
        "config": "maxRetries: 3, retryInterval: 1000ms (1s, 2s, 4s with backoff multiplier 2)",
        "fallback": "Error workflow if all retries fail",
    },
    "permanent": {
        "description": "404 not found, 400 bad request, policy violation, schema violation",
        "n8n_primitive": "IF/Switch (branch on error)",
        "config": "IF $json.error contains 'not_found' → escalate to Slack; ELSE → continue with default",
        "fallback": "Error workflow if no branch matches",
    },
    "model": {
        "description": "Hallucinated tool call, malformed output, plan contradiction",
        "n8n_primitive": "Output Parser (auto-fixing) + IF/Switch",
        "config": "Output Parser auto-fixes the model output; IF parse failed → fall back to a different model",
        "fallback": "Error workflow if all parsers fail",
    },
    "tool": {
        "description": "Tool exception, tool 500, tool returned malformed data",
        "n8n_primitive": "Continue-on-fail + IF/Switch (fallback tool)",
        "config": "Continue-on-fail: return default value; IF $json.ok is false → call fallback tool",
        "fallback": "Error workflow if fallback tool also fails",
    },
}
```

The error workflow (the 3am alert):

```
┌─────────────────┐
│  Error Trigger  │ (fires when target workflow fails)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Alert    │ (extract: execution ID, failed node, error, input)
└────────┬────────┘
         │
         ├────────────────┐
         ▼                ▼
┌─────────────┐    ┌────────────┐
│ Slack Alert │    │  Postgres  │
│ (#oncall)   │    │ (audit log)│
└─────────────┘    └────────────┘
```

The Error Trigger node configuration:

```json
{
  "name": "Error Trigger",
  "type": "n8n-nodes-base.errorTrigger",
  "parameters": {
    "workflowId": "wf-lead-enrichment"
  },
  "position": [250, 300]
}
```

The Format Alert node (Code node with JS):

```javascript
// Format the error alert
const execution = $input.item.json;
return {
  json: {
    execution_id: execution.executionId,
    workflow_name: execution.workflowName,
    failed_node: execution.lastNodeExecuted,
    error_message: execution.error?.message,
    error_type: classifyError(execution.error?.message),
    input_data: JSON.stringify(execution.data?.Webhook?.[0]?.[0]?.json || {}).slice(0, 1000),
    timestamp: new Date().toISOString(),
    slack_message: `:rotating_light: Workflow *${execution.workflowName}* failed at node *${execution.lastNodeExecuted}*.\n` +
                   `*Error:* ${execution.error?.message}\n` +
                   `*Execution ID:* ${execution.executionId}\n` +
                   `*Input:* \`\`\`${JSON.stringify(execution.data?.Webhook?.[0]?.[0]?.json || {}).slice(0, 500)}\`\`\``,
  }
};

function classifyError(message) {
  if (message?.includes('rate limit') || message?.includes('429')) return 'transient';
  if (message?.includes('not found') || message?.includes('404')) return 'permanent';
  if (message?.includes('tool call') || message?.includes('malformed')) return 'model';
  return 'tool';
}
```

The Slack Alert node:

```json
{
  "name": "Slack Alert",
  "type": "n8n-nodes-base.slack",
  "parameters": {
    "channel": "#oncall",
    "text": "={{$json.slack_message}}",
    "otherOptions": {}
  },
  "credentials": {
    "slackApi": {"id": "cred-slack", "name": "slack_workspace"}
  },
  "position": [650, 300]
}
```

The 3 retry patterns in detail:

```python
RETRY_PATTERNS = {
    "per_node": {
        "description": "Built into every node; per-node retry with backoff",
        "config": "Settings → Retry on error → Max retries: 3, Interval: 1000ms, Backoff: 2",
        "best_for": "Single-node transient errors (HTTP timeout, Postgres deadlock)",
        "example": "HTTP Request node: maxRetries: 3 → on 429, retry 1s, 2s, 4s",
    },
    "workflow_level": {
        "description": "Wrap the workflow in a 'Retry' workflow that re-runs on failure",
        "config": "Outer workflow: trigger → target workflow → on error, re-run",
        "best_for": "Transient errors that affect the whole workflow (DB connection lost)",
        "example": "Outer workflow: webhook → target → on error, re-run after 5s",
    },
    "custom": {
        "description": "Code node with custom retry logic",
        "config": "Code node: try { ... } catch { if (retries < 3) retry else fail }",
        "best_for": "Complex retry conditions (retry only on 'rate limit', not on other errors)",
        "example": "Code node: retry only on 429; give up after 3 tries; log each retry",
    },
}
```

The continue-on-fail pattern (graceful degradation):

```json
{
  "name": "Clearbit Enrichment",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "GET",
    "url": "=https://company.clearbit.com/v2/companies/find?domain={{$json.email.split('@')[1]}}",
    "continueOnFail": true,
    "options": {
      "timeout": 5000
    }
  },
  "position": [450, 300]
}
```

When `continueOnFail: true` and the HTTP Request fails (e.g., Clearbit returns 500), the node returns:
```json
{
  "error": "Request failed with status code 500",
  "json": {},
  "index": 0
}
```

The next node receives this error object and can branch on `$json.error` to handle gracefully.

The IF/Switch pattern (branch on error category):

```json
{
  "name": "IF Error",
  "type": "n8n-nodes-base.if",
  "parameters": {
    "conditions": {
      "number": [
        {
          "value1": "={{$json.error}}",
          "operation": "exists",
          "value2": "true"
        }
      ]
    }
  },
  "position": [650, 300]
}
```

The pattern that wins interviews is the "4 categories × 4 primitives + error workflow as 3am alert" pattern. The candidate who says "I map error categories to n8n primitives: transient → retry on error; permanent → IF/Switch to escalate; model → output parser + fallback model; tool → continue-on-fail + fallback tool. The error workflow is the 3am alert; it fires on any failure, sends a Slack alert, writes to the audit log. The wrong choice is to ignore errors (the workflow silently fails). The right choice is the 4 × 4 matrix + the error workflow" is the candidate who demonstrates the n8n-error-mindset.

## Code or example

The 5 most common n8n errors and fixes:

```python
N8N_ERRORS = {
    "node_credential_invalid": {
        "symptom": "Node shows 'Credential not found' or 'Invalid credential'",
        "cause": "Credential not created, wrong credential assigned, or credential rotated",
        "fix": "Settings → Credentials → verify the credential; re-assign to the node; re-authorize if OAuth",
    },
    "node_timeout": {
        "symptom": "Node shows 'Request timeout' after 30s",
        "cause": "API is slow; default timeout is 30s",
        "fix": "Set timeout: 60000 (60s) in node options; OR enable retry on error; OR enable continue-on-fail",
    },
    "expression_syntax_error": {
        "symptom": "Node shows 'Cannot read property of undefined' or 'Expression syntax error'",
        "cause": "Expression `{{$json.foo}}` references a field that doesn't exist",
        "fix": "Use `{{$json.foo || 'default'}}` for optional fields; verify the field exists in the input",
    },
    "rate_limit_exceeded": {
        "symptom": "API returns 429 Too Many Requests",
        "cause": "Too many calls in a short time",
        "fix": "Enable retry on error with exponential backoff (1s, 2s, 4s); add a Wait node between calls; reduce concurrency",
    },
    "workflow_execution_timeout": {
        "symptom": "Workflow shows 'Execution timed out' after the workflow timeout",
        "cause": "Default workflow timeout is 10 minutes; the workflow takes longer",
        "fix": "Settings → Workflow timeout → 30 minutes; OR break the workflow into smaller pieces; OR parallelize slow steps",
    },
}
```

The retry configuration for the most common nodes:

```python
RETRY_CONFIGS = {
    "http_request": {
        "maxRetries": 3,
        "retryInterval": 1000,  # 1s
        "backoffMultiplier": 2,  # 1s, 2s, 4s
        "retryOn": ["429", "500", "502", "503", "504"],
        "n8n_settings": "Settings → Retry on error → Max retries: 3, Interval: 1000ms",
    },
    "postgres": {
        "maxRetries": 2,
        "retryInterval": 500,
        "backoffMultiplier": 2,
        "retryOn": ["deadlock_detected", "connection_lost"],
        "n8n_settings": "Settings → Retry on error → Max retries: 2, Interval: 500ms",
    },
    "openai": {
        "maxRetries": 3,
        "retryInterval": 2000,  # 2s (OpenAI rate limits reset after 1-2s)
        "backoffMultiplier": 2,
        "retryOn": ["429", "500", "503"],
        "n8n_settings": "Settings → Retry on error → Max retries: 3, Interval: 2000ms",
    },
    "slack": {
        "maxRetries": 2,
        "retryInterval": 1000,
        "backoffMultiplier": 2,
        "retryOn": ["429", "500", "503"],
        "n8n_settings": "Settings → Retry on error → Max retries: 2, Interval: 1000ms",
    },
}
```

The error workflow template (the FDE's starter):

```json
{
  "name": "Error Workflow (3am Alert)",
  "nodes": [
    {
      "name": "Error Trigger",
      "type": "n8n-nodes-base.errorTrigger",
      "parameters": {"workflowId": "wf-target"},
      "position": [250, 300]
    },
    {
      "name": "Format Alert",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "mode": "runOnceForEachItem",
        "jsCode": "// Format the error alert\nconst execution = $input.item.json;\nreturn { json: { slack_message: `:rotating_light: Workflow *${execution.workflowName}* failed at node *${execution.lastNodeExecuted}*\\n*Error:* ${execution.error?.message}\\n*Execution ID:* ${execution.executionId}` } };"
      },
      "position": [450, 300]
    },
    {
      "name": "Slack Alert",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#oncall",
        "text": "={{$json.slack_message}}"
      },
      "credentials": {"slackApi": {"id": "cred-slack", "name": "slack_workspace"}},
      "position": [650, 300]
    },
    {
      "name": "Audit Log",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "INSERT INTO workflow_errors (execution_id, workflow_name, failed_node, error_message, created_at) VALUES ('{{$json.execution_id}}', '{{$json.workflow_name}}', '{{$json.failed_node}}', '{{$json.error_message}}', NOW())"
      },
      "position": [650, 500]
    }
  ],
  "connections": {
    "Error Trigger": {"main": [[{"node": "Format Alert", "type": "main", "index": 0}]]},
    "Format Alert": {"main": [[{"node": "Slack Alert", "type": "main", "index": 0}, {"node": "Audit Log", "type": "main", "index": 0}]]
  }
}
```

The Northwind error workflow (the case study):

```python
# Northwind: error workflow setup
NORTHWIND_ERROR_HANDLING = {
    "error_workflow": {
        "name": "Northwind 3am Alert",
        "trigger": "Error Trigger on all production workflows",
        "actions": [
            "Slack alert to #oncall (immediate)",
            "Postgres audit log entry (for compliance)",
            "PagerDuty incident (for SEV-1 errors)",
        ],
    },
    "per_node_retry": {
        "http_request": "maxRetries: 3, interval: 1000ms, backoff: 2 (transient errors)",
        "openai": "maxRetries: 3, interval: 2000ms, backoff: 2 (rate limits)",
        "postgres": "maxRetries: 2, interval: 500ms, backoff: 2 (deadlocks)",
    },
    "continue_on_fail": {
        "clearbit_lookup": "Return empty object; AI Agent handles missing enrichment gracefully",
        "linkedin_lookup": "Return empty object; AI Agent handles missing decision maker gracefully",
    },
    "if_switch": {
        "lead_already_in_hubspot": "IF $json.hubspot_search.found is true → skip Clearbit (saves cost)",
        "free_email_provider": "IF $json.email contains 'gmail.com' → skip enrichment, mark unqualified",
    },
    "error_rate_target": "< 1% of all workflow executions",
    "alert_threshold": "> 5 errors in 5 minutes (or any SEV-1)",
}
```

## Production addendum

The error handling question is the answer to "how do you make an n8n workflow production-ready." The 60-second script:

> "4 × 4 matrix. 4 error categories (transient, permanent, model, tool) × 4 n8n primitives (error workflow, retry, continue-on-fail, IF/Switch). Transient → retry on error (1s, 2s, 4s). Permanent → IF/Switch to escalate. Model → output parser + fallback model. Tool → continue-on-fail + fallback tool. The error workflow is the 3am alert; it fires on any failure, sends Slack to #oncall, writes to the audit log. The wrong choice is to ship without an error workflow (you don't know when things break). The right choice is the 4 × 4 matrix + the error workflow + per-node retry configs."

This is the difference between a candidate who says "I added error handling" and a candidate who says "4 × 4 matrix, error workflow as 3am alert, per-node retry configs, 5 most common errors, the continue-on-fail for graceful degradation." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/n8n/05-error-workflow.json` — the error workflow template.
- **Reference implementation**: `course/hardcode/level-9-failure-handling/17-circuit-breaker-llm.py` — the canonical error handling setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — error handling as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the MCP server's error handling parallels the n8n error workflow.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — error handling as a system design concern.

## The 3 questions this lecture preps you for

1. **"How do you make an n8n workflow production-ready?"** Answer: 4 × 4 error matrix (4 categories × 4 primitives), per-node retry configs, error workflow as the 3am alert, continue-on-fail for non-critical steps, IF/Switch for branching. The error workflow fires on any failure; sends Slack alert to #oncall; writes to audit log.
2. **"What is the error workflow as 3am alert pattern?"** Answer: every production workflow has an error workflow that fires when any node fails. The error workflow sends a Slack alert with: execution ID, failed node, error message, input data (truncated). The on-call reads the alert, opens the execution in n8n, and triages. The error workflow is not optional; it's the production-readiness contract.
3. **"What is the difference between retry and continue-on-fail?"** Answer: retry is for transient errors — the same node is retried with backoff. Continue-on-fail is for non-critical steps — the workflow continues even if the node fails, returning a default value. Retry is the right primitive for HTTP timeouts; continue-on-fail is the right primitive for optional enrichments.

## Read next

`L7-7-building-a-complete-automation.md` — the synthesis. End-to-end: lead capture → enrich → qualify → CRM → Slack. The 6-node workflow that solves Northwind's lead qualification problem.
