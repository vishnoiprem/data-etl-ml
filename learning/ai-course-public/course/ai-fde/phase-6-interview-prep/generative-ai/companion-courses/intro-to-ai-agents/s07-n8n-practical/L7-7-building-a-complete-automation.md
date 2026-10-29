# L7.7: Building a complete automation — Northwind lead qualification end-to-end

> **FDE framing in one line:** the complete automation is the synthesis of Sections 7.1-7.6. 6 nodes, 1 trigger, 3 tools, 1 AI agent, 2 outputs, 1 error workflow. The FDE who can ship this in a day is the FDE who can land the SMB engagement in a sprint. The canvas is the architecture; the execution log is the debugger; the error workflow is the 3am alert.

## In 60 seconds

> "6 nodes. Webhook → AI Agent (3 tools) → IF → HubSpot/Slack → Postgres. 3-hour build: 1 hour canvas, 1 hour system prompt, 1 hour test + error handling. 10-minute demo: 3 min build, 3 min test, 3 min Q&A, 1 min next steps. The 5 sample leads test the happy path + 4 edge cases. The runbook is the artifact that survives the FDE's exit. The wrong choice is to ship without testing or without an error workflow. The right choice is the 6 + 3 + 10 + 5 + runbook."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 6-node Northwind lead qualification workflow: Webhook → AI Agent (with 3 tools) → HubSpot → Slack → Postgres. The canvas is the architecture; each node has a single responsibility; the JSON contract is the interface.
2. The end-to-end build sequence: 1 hour for the canvas + nodes, 1 hour for the system prompt + tool definitions, 1 hour for testing + error handling. The 3-hour build is the muscle memory for the FDE's first n8n engagement.
3. The "10-minute live demo" pattern: the FDE can demo the complete workflow in 10 minutes (3 minutes build, 3 minutes test, 3 minutes Q&A, 1 minute next steps). The demo is the artifact that closes the engagement.

## Concept

The Northwind lead qualification automation is the synthesis of Sections 7.1-7.6. The workflow receives an inbound lead (via Webhook), enriches the company data (via Clearbit), qualifies the lead (via the AI Agent with 3 tools), writes to HubSpot (CRM), notifies Slack (#leads), and persists to Postgres (audit log). Six nodes, one trigger, three tools, one AI agent, two outputs, one error workflow. **The canvas is the architecture; the execution log is the debugger; the error workflow is the 3am alert.**

The 6-node workflow:

1. **Webhook trigger.** Receives the lead via HTTP POST. The body is `{"email": "alice@acme.com", "source": "website"}`. The Webhook fires the workflow.
2. **AI Agent (with 3 tools).** The orchestrator. The agent calls: (1) Clearbit Lookup (company info), (2) Lane Check (Postgres query for SG-VN support), (3) HubSpot Search (existing contact check). The agent decides which to call based on the lead. Output: a JSON object with `{qualified, score, reason}`.
3. **IF (branch on qualified).** If the agent says `qualified: true` → write to HubSpot + Slack; if `qualified: false` → just Slack notification.
4. **HubSpot (Create Contact).** If qualified, create a new contact in HubSpot with the lead's info, score, and reason. The HubSpot node is the CRM integration.
5. **Slack (Notify #leads).** Post to #leads with the lead's name, score, and reason. The Slack node is the human notification.
6. **Postgres (Audit Log).** Write the execution data to a Postgres table for the audit log. The Postgres node is the persistence layer.

The end-to-end build sequence:

1. **Hour 1: Canvas + nodes.** Drag the 6 nodes onto the canvas; wire them; configure the credentials. The 6 nodes are the architecture; the wiring is the data flow.
2. **Hour 2: System prompt + tool definitions.** Write the 5-section system prompt (from L7.4); define the 3 tools (Clearbit, Lane Check, HubSpot Search). The system prompt + tools are the agent's contract.
3. **Hour 3: Testing + error handling.** Test each node in isolation; test the workflow end-to-end; add the error workflow; add the 4 × 4 error matrix. The error handling is the production-readiness layer.

**The 3-hour build is the muscle memory for the FDE's first n8n engagement.** The FDE ships the workflow on day 1; the customer iterates on the system prompt + tools for the next 2 weeks; the FDE adds features based on feedback (more tools, more integrations, more logic).

The "10-minute live demo" pattern is the recognition that the FDE's demo is the artifact that closes the engagement. The demo is 10 minutes: 3 minutes build (drag nodes, configure), 3 minutes test (send a lead, watch the workflow), 3 minutes Q&A (the customer asks, the FDE answers), 1 minute next steps (what to do after the demo). **The demo is the FDE's sales pitch; the workflow is the proof; the customer is the judge.**

## The pattern

The 6-node Northwind workflow (the canvas):

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Webhook  │────▶│ AI Agent │────▶│ IF Qual  │────▶│ HubSpot  │
│ Trigger  │     │ (3 tools)│     │ (branch) │     │ (Create) │
└──────────┘     └─────┬────┘     └────┬─────┘     └────┬─────┘
                       │               │ (false)        │
                       │               │                │
                       │               ▼                ▼
                       │          ┌──────────┐     ┌──────────┐
                       │          │  Slack   │     │  Slack   │
                       │          │ (skip)   │     │ (notify) │
                       │          └─────┬────┘     └────┬─────┘
                       │                │               │
                       │                ▼               ▼
                       │           ┌─────────────────────────┐
                       │           │   Postgres (Audit Log)  │
                       │           └─────────────────────────┘
                       ▼
                  (3 tools, called by the agent):
            ┌──────────┬──────────┬──────────┐
            ▼          ▼          ▼
       ┌────────┐ ┌────────┐ ┌────────┐
       │Clearbit│ │  Lane  │ │HubSpot │
       │ Lookup │ │ Check  │ │ Search │
       └────────┘ └────────┘ └────────┘
```

The 6-node configuration (the full workflow):

```json
{
  "name": "Northwind Lead Qualification",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "lead",
        "responseMode": "onReceived"
      },
      "position": [250, 300]
    },
    {
      "name": "Lead Qualification Agent",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "parameters": {
        "model": "gpt-5-mini",
        "systemMessage": "You are a lead qualification agent for Northwind Logistics...\n[5-section prompt]",
        "prompt": "={{$json.email}}",
        "tools": [
          {"node": "Clearbit Lookup", "type": "@n8n/n8n-nodes-langchain.toolHttpRequest"},
          {"node": "Lane Check", "type": "@n8n/n8n-nodes-langchain.toolPostgres"},
          {"node": "HubSpot Search", "type": "@n8n/n8n-nodes-langchain.toolHttpRequest"}
        ],
        "memory": {"type": "windowBuffer", "contextWindowLength": 5},
        "maxIterations": 10,
        "outputParser": {"type": "autoFixing", "schema": "..."}
      },
      "position": [500, 300]
    },
    {
      "name": "IF Qualified",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [{"value1": "={{$json.qualified}}", "value2": true}]
        }
      },
      "position": [750, 300]
    },
    {
      "name": "HubSpot Create Contact",
      "type": "n8n-nodes-base.hubspot",
      "parameters": {
        "operation": "create",
        "resource": "contact",
        "additionalFields": {
          "email": "={{$json.email}}",
          "company": "={{$json.company}}",
          "lead_score": "={{$json.score}}",
          "qualification_reason": "={{$json.reason}}"
        }
      },
      "position": [1000, 200]
    },
    {
      "name": "Slack Notify Qualified",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#leads",
        "text": "=:zap: *Qualified lead:* {{$json.company}} (score {{$json.score}})\n*Reason:* {{$json.reason}}"
      },
      "position": [1250, 200]
    },
    {
      "name": "Slack Notify Unqualified",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#leads",
        "text": "=:x: *Unqualified lead:* {{$json.email}} (score {{$json.score}})\n*Reason:* {{$json.reason}}"
      },
      "position": [1000, 400]
    },
    {
      "name": "Postgres Audit Log",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "INSERT INTO lead_qualifications (email, company, qualified, score, reason, created_at) VALUES ('{{$json.email}}', '{{$json.company}}', {{$json.qualified}}, {{$json.score}}, '{{$json.reason}}', NOW())"
      },
      "position": [1250, 400]
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "Lead Qualification Agent", "type": "main", "index": 0}]]},
    "Lead Qualification Agent": {"main": [[{"node": "IF Qualified", "type": "main", "index": 0}]]},
    "IF Qualified": {"main": [
      [{"node": "HubSpot Create Contact", "type": "main", "index": 0}],
      [{"node": "Slack Notify Unqualified", "type": "main", "index": 0}]
    ]},
    "HubSpot Create Contact": {"main": [[{"node": "Slack Notify Qualified", "type": "main", "index": 0}]]},
    "Slack Notify Qualified": {"main": [[{"node": "Postgres Audit Log", "type": "main", "index": 0}]]},
    "Slack Notify Unqualified": {"main": [[{"node": "Postgres Audit Log", "type": "main", "index": 0}]]}
  }
}
```

The end-to-end execution (the full run):

```
[10:23:45] Webhook triggered: POST /webhook/lead
  Request body: {"email": "alice@acme.com", "source": "website"}

[10:23:45] Lead Qualification Agent (iteration 1)
  Model call: gpt-5-mini
  Input: "alice@acme.com"
  Output: "Let me check the company info first. I'll call clearbit_lookup."

[10:23:46] Clearbit Lookup (tool call)
  Args: {"email": "alice@acme.com"}
  Result: {"name": "Acme Corp", "employees": 50, "industry": "Logistics"}

[10:23:47] Lead Qualification Agent (iteration 2)
  Model call: gpt-5-mini
  Output: "Acme Corp is a mid-size logistics company. Let me check lane support."

[10:23:48] Lane Check (tool call)
  Args: {"origin": "SG", "destination": "VN"}
  Result: {"supported": true}

[10:23:49] HubSpot Search (tool call)
  Args: {"email": "alice@acme.com"}
  Result: {"found": false}

[10:23:50] Lead Qualification Agent (iteration 3)
  Model call: gpt-5-mini
  Output: {"qualified": true, "score": 75, "reason": "Mid-size logistics company, SG-VN lane supported"}

[10:23:50] IF Qualified
  Branch: true → HubSpot Create Contact

[10:23:51] HubSpot Create Contact
  Created contact ID: 12345
  Result: {"id": "12345", "email": "alice@acme.com", "company": "Acme Corp"}

[10:23:52] Slack Notify Qualified
  Message posted: ":zap: *Qualified lead:* Acme Corp (score 75)..."

[10:23:53] Postgres Audit Log
  INSERT INTO lead_qualifications... OK

[10:23:53] Workflow complete (8.2s, $0.0012)
```

The 3-hour build sequence (the FDE's first-day plan):

```python
THREE_HOUR_BUILD = {
    "hour_1_canvas_and_nodes": {
        "minute_0_10": "Install n8n; create workflow 'Northwind Lead Qualification'",
        "minute_10_20": "Drag Webhook trigger; configure POST /lead",
        "minute_20_30": "Drag AI Agent node; wire Webhook → AI Agent",
        "minute_30_50": "Drag 3 tool nodes (Clearbit, Lane Check, HubSpot Search); wire to AI Agent",
        "minute_50_60": "Drag IF node; drag HubSpot + Slack + Postgres nodes; wire the branches",
        "deliverable": "Working canvas with 6 nodes; all nodes wired; all credentials configured",
    },
    "hour_2_system_prompt_and_tools": {
        "minute_0_30": "Write the 5-section system prompt (Role, Tools, Output Format, Guardrails, Examples)",
        "minute_30_45": "Configure the AI Agent: model=gpt-5-mini, max iterations=10, output parser=auto-fixing",
        "minute_45_60": "Configure the 3 tools: Clearbit (HTTP), Lane Check (Postgres), HubSpot Search (HTTP)",
        "deliverable": "Working agent that calls the 3 tools correctly; output is structured JSON",
    },
    "hour_3_testing_and_error_handling": {
        "minute_0_20": "Test each node in isolation (Webhook, AI Agent, IF, HubSpot, Slack, Postgres)",
        "minute_20_40": "Test the workflow end-to-end with 5 sample leads (qualified, unqualified, free email, etc.)",
        "minute_40_55": "Add the error workflow (3am alert to #oncall + Postgres audit log)",
        "minute_55_60": "Add per-node retry configs (HTTP: 3 retries, OpenAI: 3 retries, Postgres: 2 retries)",
        "deliverable": "Production-ready workflow that handles errors gracefully + alerts the on-call",
    },
}
```

The 10-minute live demo script (the FDE's sales pitch):

```python
TEN_MINUTE_DEMO = {
    "minute_0_3_build": {
        "script": "Watch me build the workflow in 3 minutes. I drag a Webhook, an AI Agent with 3 tools, an IF, a HubSpot node, and a Slack node. 6 nodes. The system prompt is a 5-section template: Role, Tools, Output Format, Guardrails, Examples. The 3 tools are Clearbit, Lane Check, HubSpot Search. Done.",
        "deliverable": "The customer sees the canvas; the architecture is visible",
    },
    "minute_3_6_test": {
        "script": "Now let me send a test lead. *runs curl POST /webhook/lead with alice@acme.com*. Watch the execution log: the agent called Clearbit, got the company info, checked lane support, found the lead wasn't in HubSpot, and qualified with score 75. Slack message posted. Postgres audit log written. Total time: 8.2 seconds. Cost: $0.0012.",
        "deliverable": "The customer sees the agent work end-to-end; the result is visible",
    },
    "minute_6_9_qa": {
        "script": "What questions do you have? *pauses for Q&A*",
        "common_q": [
            "What if Clearbit is down? → Continue-on-fail; agent uses partial data",
            "What if the lead is from a free email? → Guardrail in system prompt returns score 0",
            "What if HubSpot is down? → IF Qualified still works; just no CRM write",
            "What about cost? → $0.0012 per lead; $0.24/day for 200 leads; $7.20/month",
            "What about error handling? → Error workflow sends Slack alert to #oncall",
        ],
        "deliverable": "The customer asks hard questions; the FDE answers with specifics",
    },
    "minute_9_10_next_steps": {
        "script": "If you want this in production, here's the plan: Week 1, I build the workflow (today's demo). Week 2, I add more tools (LinkedIn enrichment, email validation). Week 3, I add a feedback loop (track which leads convert). Week 4, I hand off to your team with the runbook. Total: 4 weeks, $20K. Questions?",
        "deliverable": "The customer knows the next steps; the FDE has a proposal ready",
    },
}
```

The pattern that wins interviews is the "6 nodes + 3-hour build + 10-minute demo" pattern. The candidate who says "I build the complete lead qualification workflow in 3 hours (1 hour canvas, 1 hour prompt, 1 hour test + error handling). I demo in 10 minutes (3 min build, 3 min test, 3 min Q&A, 1 min next steps). The 6 nodes are: Webhook → AI Agent (3 tools) → IF → HubSpot/Slack → Postgres. The wrong choice is to ship without an error workflow or without testing. The right choice is the 6 + 3 + 10" is the candidate who demonstrates the n8n-ship-mindset.

## Code or example

The 5 sample leads (the test suite):

```python
SAMPLE_LEADS = [
    {
        "name": "Qualified mid-size",
        "input": {"email": "alice@acme.com", "source": "website"},
        "expected": {"qualified": True, "score_range": (60, 90)},
        "tests": ["Clearbit called", "Lane Check called", "HubSpot Search called", "Slack notified", "HubSpot contact created", "Postgres audit log written"],
    },
    {
        "name": "Free email provider",
        "input": {"email": "bob@gmail.com", "source": "website"},
        "expected": {"qualified": False, "score": 0},
        "tests": ["No tool calls (guardrail triggers early)", "Slack notified (unqualified)", "HubSpot NOT created", "Postgres audit log written"],
    },
    {
        "name": "Lane not supported",
        "input": {"email": "carol@bigcompany.com", "source": "linkedin"},
        "expected": {"qualified": False, "score_range": (20, 50)},
        "tests": ["Clearbit called", "Lane Check called (US-MX not supported)", "Slack notified (unqualified)", "Postgres audit log written"],
    },
    {
        "name": "Already in HubSpot",
        "input": {"email": "dan@existing.com", "source": "referral"},
        "expected": {"qualified": True, "score_range": (70, 90)},
        "tests": ["Clearbit called", "HubSpot Search called (found)", "HubSpot contact UPDATED (not created)", "Postgres audit log written"],
    },
    {
        "name": "Clearbit down",
        "input": {"email": "eve@unknown.com", "source": "website"},
        "expected": {"qualified": False, "score_range": (0, 30)},
        "tests": ["Clearbit returns 500 (continue-on-fail)", "Lane Check still called", "Slack notified (unqualified, low data)", "Postgres audit log written"],
    },
]
```

The Northwind KPIs (the metrics the FDE tracks):

```python
NORTHWIND_KPIS = {
    "workflow_success_rate": {"target": "> 99%", "current": "99.5%"},
    "workflow_latency_p95": {"target": "< 15s", "current": "8.2s"},
    "cost_per_lead": {"target": "< $0.005", "current": "$0.0012"},
    "daily_cost": {"target": "< $5", "current": "$0.24 (200 leads)"},
    "monthly_cost": {"target": "< $100", "current": "$7.20"},
    "qualified_leads_per_day": {"target": "> 50", "current": "73"},
    "false_positive_rate": {"target": "< 10%", "current": "8% (manual review)"},
    "false_negative_rate": {"target": "< 5%", "current": "3% (manual review)"},
    "error_workflow_alerts": {"target": "< 5/day", "current": "1.2/day"},
    "manual_review_hours_saved": {"target": "> 3 hours/day", "current": "4.5 hours/day"},
}
```

The Northwind runbook (the FDE's first artifact):

```markdown
# Northwind Lead Qualification Runbook

## Workflow: Lead Qualification
**Trigger:** POST /webhook/lead
**Expected latency:** < 15s (p95)
**Expected cost:** < $0.005 per lead
**Expected volume:** 200 leads/day

## Common Alerts

### Alert: workflow_success_rate < 95%
1. Check the error workflow Slack channel (#oncall)
2. Identify the most common error (Clearbit 500, OpenAI 429, HubSpot 401)
3. Apply the matching recovery (from the 4 × 4 matrix)
4. Page the FDE on-call if not resolved in 30 min

### Alert: cost_per_lead > $0.01
1. Check the execution log for high-cost iterations
2. Identify the model that drove the cost (likely GPT-5 instead of GPT-5-mini)
3. Update the AI Agent to use GPT-5-mini for routine steps
4. Re-test with the 5 sample leads

### Alert: qualified_leads_per_day < 30
1. Check the false negative rate in the Postgres audit log
2. Sample 10 unqualified leads; check if the agent's reasoning is correct
3. Update the system prompt's guardrails or examples
4. Re-test; re-deploy

## Maintenance

### Daily
- Check the error workflow Slack channel
- Verify the success rate is > 99%
- Verify the cost is < $5

### Weekly
- Review the 5 most recent errors; identify patterns
- Update the system prompt based on edge cases
- Re-test with the 5 sample leads

### Monthly
- Rotate the API keys (Clearbit, OpenAI, HubSpot)
- Review the cost and adjust the model if needed
- Add new tools based on customer feedback
```

## Production addendum

The complete automation question is the answer to "show me you can ship a production workflow in n8n." The 60-second script:

> "6 nodes. Webhook → AI Agent (3 tools) → IF → HubSpot/Slack → Postgres. 3-hour build: 1 hour canvas, 1 hour system prompt, 1 hour test + error handling. 10-minute demo: 3 min build, 3 min test, 3 min Q&A, 1 min next steps. The 5 sample leads test the happy path + 4 edge cases. The runbook is the artifact that survives the FDE's exit. The wrong choice is to ship without testing or without an error workflow. The right choice is the 6 + 3 + 10 + 5 + runbook."

This is the difference between a candidate who says "I built an n8n workflow" and a candidate who says "6 nodes, 3-hour build, 10-minute demo, 5 sample leads, runbook as the artifact, the canvas is the architecture." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/n8n/06-northwind-workflow.json` — the full workflow export.
- **Reference implementation**: `course/hardcode/level-2-ai-workflows/03-email-triage-pipeline.py` — the canonical end-to-end build.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — n8n as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the MCP server parallels the n8n tool nodes.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — n8n as a system design choice.

## The 3 questions this lecture preps you for

1. **"Show me you can ship a production workflow in n8n."** Answer: 6 nodes (Webhook → AI Agent with 3 tools → IF → HubSpot/Slack → Postgres). 3-hour build (1 hour canvas, 1 hour prompt, 1 hour test). 10-minute demo. 5 sample leads covering happy path + 4 edge cases. Runbook as the artifact.
2. **"What is the canvas as architecture pattern?"** Answer: the visual layout of the workflow is the documentation. 6 nodes, left-to-right (trigger → processing → output), consistent naming, clear JSON contract between nodes. The wrong choice is spaghetti workflows with 30 unlabeled nodes. The right choice is the readable canvas + the explicit JSON contract.
3. **"How do you demo an n8n workflow in 10 minutes?"** Answer: 3 min build (drag 6 nodes, configure), 3 min test (send a lead, watch the execution), 3 min Q&A (answer hard questions: Clearbit down, free email, HubSpot down, cost, error handling), 1 min next steps (the 4-week plan, $20K). The demo is the FDE's sales pitch; the workflow is the proof.

## Read next

`L7-8-when-to-use-n8n-vs-code.md` — the platform decision rubric. 4 axes: team (engineering-first or not), scale (concurrent runs), latency (sub-second or not), cost (infrastructure vs developer time). The FDE picks the platform that matches the customer's requirements.
