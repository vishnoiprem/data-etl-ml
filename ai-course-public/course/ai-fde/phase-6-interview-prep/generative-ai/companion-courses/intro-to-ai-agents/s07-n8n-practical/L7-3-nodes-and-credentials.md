# L7.3: Nodes and credentials — the 1000+ node library and the secret-keeping discipline

> **FDE framing in one line:** n8n ships 1000+ pre-built nodes for the services your customer already uses. The FDE's job is to know which node maps to which service, and to never paste an API key into a node's parameters. The credential is the FDE's secret-keeping discipline.

## The 3 things you'll learn

1. The 4 node categories: trigger nodes (start the workflow), data nodes (transform data), action nodes (call an API), logic nodes (branch, merge, loop). Each category has a specific role; the FDE picks the right category for the right job.
2. The 3 credential types: API key (single token), OAuth (authorization flow), database (connection string). The credential is created once, referenced by every node that needs it, and encrypted at rest. The FDE never embeds secrets in node parameters.
3. The "credential redaction" pattern: the FDE's discipline is to never log the credential, never paste it in chat, never commit it to git. The n8n audit log redacts the credential by default; the FDE must not bypass this.

## Concept

n8n ships 1000+ pre-built nodes for the most common services: Slack, Salesforce, HubSpot, Postgres, MySQL, OpenAI, Anthropic, Google Sheets, Notion, Airtable, Jira, Linear, GitHub, Stripe, Twilio, SendGrid, S3, Google Cloud Storage, and hundreds more. Each node encapsulates the API of one service: the FDE configures the node (URL, method, parameters), the node handles the API call (auth, retry, pagination, rate limit). **The FDE does not write API code; the FDE configures the node.**

The 4 node categories:

1. **Trigger nodes.** Start the workflow. There is exactly one trigger per workflow. Examples: Webhook (HTTP POST), Schedule (cron), Email Trigger (IMAP), Database Trigger (new row), Slack Trigger (new message). The trigger is the entry point; the FDE picks the trigger that matches the customer's data source.
2. **Data nodes.** Transform data. Examples: Set (add/remove fields), Code (run JavaScript or Python), Item Lists (split, aggregate, sort), Date Time (format, parse, modify), Crypto (hash, sign, encrypt). The data node is the FDE's "data shaping" tool; it sits between the trigger and the action nodes.
3. **Action nodes.** Call an API. Examples: HTTP Request (any API), Slack (send message), Postgres (execute query), HubSpot (create contact), OpenAI (call model), Anthropic (call model), Google Sheets (read/write row). The action node does the work; the FDE picks the action that matches the customer's destination.
4. **Logic nodes.** Control flow. Examples: IF (branch on condition), Switch (multiple branches), Merge (combine branches), Loop (iterate), Wait (pause), Error Trigger (catch failures). The logic node is the FDE's "control flow" tool; it sits between action nodes to express conditional logic.

The 3 credential types:

1. **API key.** A single token. The FDE creates the credential by pasting the API key into n8n; n8n encrypts it and stores it. Every node that uses the API references the credential by name. The API key is the simplest credential type; it's the right choice for services that issue long-lived tokens (OpenAI, Anthropic, Clearbit, Stripe).
2. **OAuth.** An authorization flow. The FDE creates the credential by clicking "Connect" and authorizing n8n to access the service on the user's behalf; n8n stores the access + refresh tokens. The OAuth credential is the right choice for services that delegate access (Slack, Google, HubSpot, Salesforce, GitHub). The OAuth flow handles token refresh automatically.
3. **Database.** A connection string. The FDE creates the credential by providing the host, port, database, username, and password; n8n stores the connection string. The database credential is the right choice for Postgres, MySQL, MongoDB, Redis, and SQL Server. The connection is established on each node execution; the connection is pooled within the workflow.

The "credential redaction" pattern is the FDE's discipline:

1. **Never paste a credential in a node's parameters.** If a node requires an API key, the FDE creates a credential and selects it from the dropdown. The FDE does not paste the key into a "value" field.
2. **Never log a credential.** n8n redacts credentials from the execution log by default. The FDE must not turn off redaction. The FDE must not paste a credential into a Code node's `console.log()`.
3. **Never commit a credential to git.** n8n workflows are stored in `~/.n8n/workflows/` (self-hosted) or in the n8n database (cloud). The FDE does not commit the workflow JSON to git if it contains credentials; the FDE exports the workflow without credentials and commits the sanitized JSON.
4. **Rotate credentials on team changes.** When a team member leaves, the FDE rotates every credential they had access to. The rotation is a one-time task; the discipline is to do it on the day the team member leaves, not on the day a breach is discovered.

**The credential is the FDE's secret-keeping discipline; the pattern is the same whether the FDE is using n8n, Python, or any other platform.** The n8n-specific layer is that n8n redacts by default; the FDE's job is to not bypass the redaction.

## The pattern

The 4 node categories in action (the canonical workflow with all 4):

```
┌──────────┐  ┌──────┐  ┌──────────────┐  ┌──────┐  ┌────────┐
│ Webhook  │─▶│  IF  │─▶│ HTTP Request │─▶│  Set │─▶│ Slack  │
│ Trigger  │  │      │  │   (Clearbit) │  │      │  │        │
└──────────┘  └──┬───┘  └──────────────┘  └──────┘  └────────┘
                │ (false)
                ▼
            ┌────────┐
            │ Slack  │
            │ (warn) │
            └────────┘
```

- **Trigger:** Webhook (data source)
- **Logic:** IF (branch: company has > 10 employees)
- **Action:** HTTP Request (enrich with Clearbit)
- **Data:** Set (add timestamp + source)
- **Action:** Slack (notify #leads)

The 3 credential types in action:

```python
CREDENTIAL_TYPES = {
    "api_key": {
        "examples": ["OpenAI", "Anthropic", "Clearbit", "Stripe", "Twilio"],
        "setup": "Paste the API key into n8n; n8n encrypts + stores",
        "rotation": "Generate a new key in the service's dashboard; replace in n8n",
        "lifetime": "Long-lived (90+ days); some services allow indefinite",
    },
    "oauth": {
        "examples": ["Slack", "Google Sheets", "HubSpot", "Salesforce", "GitHub", "Notion"],
        "setup": "Click 'Connect'; authorize n8n; n8n stores access + refresh tokens",
        "rotation": "Re-authorize when the token expires (typically 30-90 days)",
        "lifetime": "Short-lived access token + long-lived refresh token",
    },
    "database": {
        "examples": ["Postgres", "MySQL", "MongoDB", "Redis", "SQL Server"],
        "setup": "Provide host + port + database + username + password; n8n tests the connection",
        "rotation": "Update the password in the database; update in n8n",
        "lifetime": "Until the password is rotated",
    },
}
```

The credential redaction pattern (the FDE's discipline):

```python
CREDENTIAL_REDACTION_RULES = {
    "rule_1_never_paste": {
        "description": "Never paste a credential in a node's parameters",
        "example_bad": "HTTP Request node: 'Authorization: Bearer sk-abc123...'",
        "example_good": "HTTP Request node: 'Authentication: Predefined Credential Type' → 'OpenAI API'",
    },
    "rule_2_never_log": {
        "description": "Never log a credential in a Code node or in a comment",
        "example_bad": "console.log('API key:', apiKey);",
        "example_good": "console.log('API call succeeded');",
    },
    "rule_3_never_commit": {
        "description": "Never commit a credential to git; export workflows without credentials",
        "example_bad": "git add workflows/lead-enrichment.json (contains the OpenAI key)",
        "example_good": "n8n export --include-credentials=false lead-enrichment.json",
    },
    "rule_4_rotate_on_team_change": {
        "description": "Rotate every credential when a team member with access leaves",
        "frequency": "On the day of departure, not on the day of the breach",
        "checklist": "1. List all credentials; 2. Rotate each in the service's dashboard; 3. Update in n8n; 4. Test the workflow",
    },
}
```

The 10 most-used n8n nodes (the FDE's reference):

```python
MOST_USED_NODES = {
    "trigger": [
        ("Webhook", "Receive HTTP requests; the most common trigger"),
        ("Schedule", "Cron-based triggers; daily, hourly, every 5 minutes"),
        ("Email Trigger", "IMAP; new email arrives; the right trigger for email-based automations"),
        ("Slack Trigger", "New message in a channel; the right trigger for Slack-based automations"),
    ],
    "data": [
        ("Set", "Add/remove/rename fields; the most common data transformation"),
        ("Code", "Run JavaScript or Python; the escape hatch when no node does what you need"),
        ("Item Lists", "Split, aggregate, sort; the right node for batch processing"),
        ("Date Time", "Format, parse, modify dates; the right node for time math"),
    ],
    "action": [
        ("HTTP Request", "Call any API; the most flexible action node"),
        ("OpenAI", "Call GPT-5, GPT-5-mini; the right action for LLM calls"),
        ("Anthropic", "Call Claude Sonnet 4.5, Claude Haiku 4.5; the right action for Claude"),
        ("Postgres", "Execute SQL; the right action for database reads/writes"),
    ],
    "logic": [
        ("IF", "Branch on a condition; the most common logic node"),
        ("Switch", "Multiple branches; the right node for N-way routing"),
        ("Merge", "Combine branches; the right node for fan-in"),
        ("Wait", "Pause execution; the right node for rate limiting or scheduled delays"),
    ],
}
```

The pattern that wins interviews is the "4 categories + 3 credential types + redaction discipline" pattern. The candidate who says "I use 4 node categories (trigger, data, action, logic) and 3 credential types (API key, OAuth, database). The credential is created once, referenced by every node, encrypted at rest. The redaction discipline: never paste, never log, never commit, rotate on team change. The wrong choice is to embed credentials in node parameters. The right choice is the 4 + 3 + 4-rule discipline" is the candidate who demonstrates the n8n-security-mindset.

## Code or example

The credential creation flow (the FDE's steps):

```markdown
# Creating an OpenAI credential in n8n

## Step 1: Get the API key
- Go to https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy the key (starts with `sk-...`)

## Step 2: Create the credential in n8n
- In n8n, go to Settings → Credentials
- Click "New"
- Search for "OpenAI"
- Select "OpenAI API"
- Paste the API key
- Click "Save"

## Step 3: Use the credential in a node
- Drag an OpenAI node onto the canvas
- In the credential dropdown, select "OpenAI API"
- The node is now authenticated

## Step 4: Test
- Click "Execute Node" on the OpenAI node
- Verify: the model returns a response
- The API key is never displayed in the node's parameters or in the execution log
```

The credential redaction in the execution log (what the FDE sees):

```json
{
  "node": "OpenAI",
  "input": {
    "model": "gpt-5-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  },
  "output": {
    "choices": [{"message": {"role": "assistant", "content": "Hi there!"}}]
  },
  "credentials": {
    "openaiApi": {
      "id": "cred-openai-1",
      "name": "OpenAI Production",
      "type": "openaiApi",
      "displayName": "OpenAI API"
    }
  }
}
```

Note: the credential is referenced by ID + name + type, but the API key is never displayed. The n8n execution log redacts the key by default.

The 4 most common credential errors and fixes:

```python
CREDENTIAL_ERRORS = {
    "credential_not_found": {
        "symptom": "Node shows 'No credential' or 'Credential not found'",
        "cause": "Credential not created or not assigned to the node",
        "fix": "Go to Settings → Credentials; create the credential; assign to the node",
    },
    "credential_invalid": {
        "symptom": "API returns 401 Unauthorized",
        "cause": "API key is wrong, expired, or rotated",
        "fix": "Verify the key in the service's dashboard; if wrong, create a new credential in n8n; if rotated, update the credential",
    },
    "credential_rate_limited": {
        "symptom": "API returns 429 Too Many Requests",
        "cause": "The credential is being rate-limited by the service",
        "fix": "Add a Wait node between calls; use the rate limiter; consider a different credential with higher limits",
    },
    "credential_oauth_expired": {
        "symptom": "API returns 401 after weeks of working",
        "cause": "OAuth refresh token expired; n8n cannot refresh automatically",
        "fix": "Re-authorize the credential; click 'Reconnect' on the credential in n8n",
    },
}
```

The Northwind credentials inventory (the case study):

```python
# Northwind Logistics: credentials inventory
NORTHWIND_CREDENTIALS = {
    "openai_api": {
        "type": "api_key",
        "owner": "prem@northwind.com",
        "rotated": "2026-09-01",
        "next_rotation": "2026-12-01",
        "monthly_cost": "$50",
    },
    "slack_workspace": {
        "type": "oauth",
        "owner": "prem@northwind.com",
        "authorized_at": "2026-08-15",
        "channels": ["#leads", "#ops", "#alerts"],
    },
    "hubspot_prod": {
        "type": "oauth",
        "owner": "prem@northwind.com",
        "authorized_at": "2026-08-15",
        "scopes": ["contacts", "deals", "companies"],
    },
    "clearbit_api": {
        "type": "api_key",
        "owner": "prem@northwind.com",
        "rotated": "2026-09-01",
        "monthly_calls": "5,000 / 50,000 limit",
    },
    "postgres_main": {
        "type": "database",
        "host": "db.northwind.internal",
        "owner": "daniel@northwind.com",
        "rotated": "2026-08-01",
    },
}
```

## Production addendum

The credentials question is the answer to "how do you handle secrets in n8n." The 60-second script:

> "3 credential types. API key (paste once, encrypted, referenced by every node). OAuth (authorize once, refresh tokens auto-managed). Database (connection string, pooled per execution). The 4-rule redaction discipline: never paste in node parameters, never log, never commit to git, rotate on team change. n8n redacts by default; the FDE must not bypass. The wrong choice is to embed the API key in the HTTP Request node's headers. The right choice is the credential object + the 4-rule discipline."

This is the difference between a candidate who says "I configured the API key" and a candidate who says "3 credential types, encrypted at rest, 4-rule redaction discipline, the credential is the FDE's secret-keeping discipline." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-applications/n8n/02-credentials.json` — the credential inventory template.
- **Reference implementation**: `course/hardcode/level-7-n8n/02-credentials.md` — the canonical credential setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/16-secrets-management.md` — secrets as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/` — the MCP server's policy file parallels the n8n credential.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/10-low-code-platforms.md` — credentials as a system design concern.

## The 3 questions this lecture preps you for

1. **"How do you handle secrets in n8n?"** Answer: 3 credential types (API key, OAuth, database) stored encrypted at rest, referenced by every node that needs them. The 4-rule redaction discipline: never paste in node parameters, never log, never commit to git, rotate on team change. n8n redacts by default; the FDE must not bypass.
2. **"What are the 4 node categories?"** Answer: trigger (start the workflow), data (transform data), action (call an API), logic (branch, merge, loop). Each category has a specific role; the FDE picks the right category for the right job. The 10 most-used nodes are: Webhook, Schedule, Set, Code, HTTP Request, OpenAI, Anthropic, Postgres, IF, Switch.
3. **"What happens when a credential is rotated?"** Answer: the FDE updates the credential in n8n; the next node execution uses the new credential; the old credential is invalidated. For OAuth, the FDE clicks "Reconnect" to re-authorize. For database, the FDE updates the password. The workflow does not need to be redeployed; the credential update is immediate.

## Read next

`L7-4-the-ai-agent-node.md` — the AI Agent node: the model selector, the system prompt, the tools, the memory. The n8n implementation of the 7 ingredients from Section 2.
