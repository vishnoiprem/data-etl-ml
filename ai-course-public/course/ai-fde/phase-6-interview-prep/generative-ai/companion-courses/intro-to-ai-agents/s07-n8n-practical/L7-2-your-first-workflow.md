# L7.2: Your first workflow — Webhook → HTTP → Slack in 10 minutes

> **FDE framing in one line:** the first workflow is the proof that n8n works. Trigger (Webhook) → enrichment (HTTP Request) → output (Slack). Three nodes, three edges, one execution. The FDE who can ship this in 10 minutes is the FDE who can scope the next engagement in 10 days.

## The 3 things you'll learn

1. The 3-node starter workflow: Webhook (trigger) → HTTP Request (enrich) → Slack (notify). Each node has a single responsibility; the JSON contract between them is the interface.
2. The 4-step build process: install n8n, create a workflow, add 3 nodes, test. The first 10 minutes is the same for every n8n project; the 4 steps are the muscle memory.
3. The "test as you build" pattern: the FDE runs each node individually before wiring them. Test → Set → Test → HTTP → Test → Slack. The test-as-you-build is the discipline that catches the bug at the right layer.

## Concept

The first n8n workflow is the same for every FDE: prove the platform works by building a 3-node pipeline that does something useful. The canonical first workflow is **Webhook → HTTP Request → Slack**: receive a webhook (someone fills out a form), enrich the data via HTTP (call Clearbit to get the company name), notify Slack (post to #leads). Three nodes, three responsibilities, one execution.

The 3 nodes:

1. **Webhook trigger.** Listens for an HTTP POST at a specific path. The body of the POST becomes `$json`. The FDE tests the webhook by sending a `curl` POST; the JSON appears in the Webhook node's output. **The webhook is the entry point; the JSON body is the input contract.**
2. **HTTP Request.** Calls an external API. The FDE configures the URL, the method, the headers, and the body. The HTTP Request node can read from `$json` to build the request (e.g., `{{$json.email}}` as a query param). The response becomes `$json`. **The HTTP Request is the enrichment; the response is the output contract.**
3. **Slack.** Posts a message to a channel. The FDE configures the credential (Slack OAuth), the channel, and the message text. The Slack node reads from `$json` to build the message. **The Slack node is the output; the message is the artifact.**

The 4-step build process:

1. **Install n8n.** `npx n8n` or `npm install n8n -g && n8n start`. Default URL: http://localhost:5678. The FDE creates an account on first visit.
2. **Create a workflow.** Click "New Workflow". The canvas is empty. The FDE names the workflow ("Lead Enrichment") and adds a description.
3. **Add 3 nodes.** Drag Webhook, HTTP Request, and Slack onto the canvas. Wire them: Webhook → HTTP Request → Slack. Configure each node's parameters.
4. **Test.** Click "Execute Workflow" (manual run) or "Listen for test event" (for the Webhook). Send a `curl` POST to the webhook URL. Verify the Slack message arrives. **The test is the gate; the workflow is not done until the test passes.**

The "test as you build" pattern is the recognition that the FDE should not wait until the entire workflow is built to test. The FDE tests each node individually:

1. Test the Webhook: send a `curl` POST; verify the JSON appears in the Webhook node's output.
2. Test the HTTP Request: configure with sample data; click "Execute Node"; verify the response is correct.
3. Test the Slack: configure with a test message; click "Execute Node"; verify the message arrives in Slack.
4. Test the workflow: send a `curl` POST; verify the entire pipeline runs end-to-end.

**Testing each node in isolation catches the bug at the right layer.** A bug in the HTTP Request is a bug in the API call, not in Slack; a bug in Slack is a bug in the credential, not in the HTTP Request. The FDE's first 10 minutes with n8n is muscle memory for this 4-step build + the 4-test pattern.

## The pattern

The 3-node starter workflow (the canonical first build):

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│ Webhook  │────▶│ HTTP Request │────▶│  Slack   │
│ Trigger  │     │  (Clearbit)  │     │  (Post)  │
└──────────┘     └──────────────┘     └──────────┘
   $json:           $json:                $json:
   {                 {                     {
     "email":          "email":              "channel":
      "alice@...        "alice@...",         "#leads",
   }                   "company":            "text":
                        "Acme Corp",         "Acme Corp
                        "employees":         (50 employees)
                          50                }
                      }                   
```

The Webhook node configuration:

```json
{
  "name": "Webhook",
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "httpMethod": "POST",
    "path": "lead",
    "responseMode": "onReceived",
    "responseData": "allEntries",
    "options": {}
  },
  "position": [250, 300]
}
```

The HTTP Request node configuration (calls Clearbit):

```json
{
  "name": "Clearbit Enrichment",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "GET",
    "url": "=https://company.clearbit.com/v2/companies/find?domain={{$json.email.split('@')[1]}}",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "clearbitApi",
    "options": {
      "timeout": 10000
    }
  },
  "position": [450, 300]
}
```

The Slack node configuration:

```json
{
  "name": "Slack Notification",
  "type": "n8n-nodes-base.slack",
  "parameters": {
    "channel": "#leads",
    "text": "=:zap: New lead: *{{$node['Clearbit Enrichment'].json.name}}* (={{$node['Clearbit Enrichment'].json.metrics.employees}} employees)",
    "otherOptions": {}
  },
  "credentials": {
    "slackApi": {"id": "cred-slack", "name": "slack_workspace"}
  },
  "position": [650, 300]
}
```

The execution log (what the FDE reads to verify):

```
[10:23:45] Webhook triggered: POST /webhook/lead
  Request body: {"email": "alice@acme.com"}
[10:23:45] HTTP Request executed
  Response: {"name": "Acme Corp", "domain": "acme.com", "metrics": {"employees": 50}}
[10:23:46] Slack executed
  Response: {"ok": true, "channel": "#leads", "ts": "1234567890.123456"}
[10:23:46] Workflow complete (1.2s)
```

The test commands the FDE uses:

```bash
# Test the webhook from the command line
curl -X POST http://localhost:5678/webhook/lead \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@acme.com"}'

# Expected: 200 OK, Slack message arrives in #leads within 1-2 seconds

# Test the webhook with multiple leads
for email in alice@acme.com bob@beta.com carol@gamma.com; do
  curl -X POST http://localhost:5678/webhook/lead \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$email\"}"
done
# Expected: 3 Slack messages arrive in #leads

# Test the HTTP Request in isolation
# In n8n: click on the HTTP Request node → click "Execute Node"
# Expected: Clearbit response in the node's output

# Test the Slack in isolation
# In n8n: click on the Slack node → click "Execute Node"
# Expected: a test message arrives in #leads
```

The pattern that wins interviews is the "3 nodes + 4 steps + test-as-you-build" pattern. The candidate who says "I build the first n8n workflow in 4 steps: install, create, add 3 nodes, test. I test each node in isolation before wiring them. The 3-node starter (Webhook → HTTP → Slack) is the proof that the platform works; the rest of the engagement is scaling this pattern. The wrong choice is to build the entire workflow and test at the end (you don't know which node failed). The right choice is the 3 + 4 + test-as-you-build" is the candidate who demonstrates the n8n-builder-mindset.

## Code or example

The 10-minute build checklist:

```markdown
# n8n First Workflow Build Checklist (10 minutes)

## Minute 0-2: Install + Setup
- [ ] Run `npx n8n` (or `npx n8n --tunnel` for webhook testing)
- [ ] Open http://localhost:5678
- [ ] Create account
- [ ] Create new workflow: "Lead Enrichment"

## Minute 2-4: Webhook Trigger
- [ ] Drag Webhook node onto canvas
- [ ] Configure: POST method, path "lead", response mode "onReceived"
- [ ] Click "Listen for test event"
- [ ] Run: `curl -X POST http://localhost:5678/webhook-test/lead -H "Content-Type: application/json" -d '{"email":"alice@acme.com"}'`
- [ ] Verify: Webhook node shows the JSON in its output

## Minute 4-6: HTTP Request
- [ ] Drag HTTP Request node onto canvas
- [ ] Wire Webhook → HTTP Request
- [ ] Configure: GET method, URL with `{{$json.email.split('@')[1]}}` as domain
- [ ] Add Clearbit credential (API key)
- [ ] Click "Execute Node" (uses sample data)
- [ ] Verify: HTTP Request node shows the Clearbit response

## Minute 6-8: Slack
- [ ] Drag Slack node onto canvas
- [ ] Wire HTTP Request → Slack
- [ ] Configure: channel #leads, text with `{{$node['HTTP Request'].json.name}}`
- [ ] Add Slack credential (OAuth)
- [ ] Click "Execute Node"
- [ ] Verify: Slack message arrives in #leads

## Minute 8-10: End-to-End Test
- [ ] Save the workflow
- [ ] Click "Listen for test event" on the Webhook
- [ ] Run: `curl -X POST http://localhost:5678/webhook-test/lead -H "Content-Type: application/json" -d '{"email":"bob@beta.com"}'`
- [ ] Verify: Slack message arrives in #leads with "Beta Corp"
- [ ] Activate the workflow (toggle "Active")
- [ ] Run: `curl -X POST http://localhost:5678/webhook/lead -H "Content-Type: application/json" -d '{"email":"carol@gamma.com"}'`
- [ ] Verify: Slack message arrives in #leads (production webhook)
```

The 4 common first-workflow errors and fixes:

```python
FIRST_WORKFLOW_ERRORS = {
    "webhook_404": {
        "symptom": "curl returns 404",
        "cause": "Wrong webhook URL; using `/webhook-test/` for production or vice versa",
        "fix": "Use `/webhook-test/` for testing (with 'Listen for test event' on); use `/webhook/` for production (with workflow activated)",
    },
    "http_request_undefined": {
        "symptom": "HTTP Request node shows `undefined` in URL",
        "cause": "Trying to read `$json.email` before the Webhook node has run",
        "fix": "Test the Webhook first; verify the JSON appears; THEN run the HTTP Request",
    },
    "slack_credential_missing": {
        "symptom": "Slack node shows 'No credential'",
        "cause": "Credential not created or not assigned to the node",
        "fix": "Go to Credentials → New → Slack OAuth → authorize; THEN assign to the Slack node",
    },
    "slack_channel_not_found": {
        "symptom": "Slack returns 'channel_not_found'",
        "cause": "Channel name typo or bot not invited to channel",
        "fix": "Verify the channel exists; invite the bot to the channel (`/invite @n8n-bot` in Slack)",
    },
}
```

The Northwind first workflow (the case study):

```python
# Northwind Logistics: Lead Enrichment
# Trigger: Webhook (POST /lead)
# Input: {"email": "alice@acme.com"}
# Enrichment: Clearbit (company info) + LinkedIn (decision maker)
# Output: Slack message in #leads with company name + decision maker

# The 3-node build (10 minutes):
# 1. Webhook: POST /lead, body is {"email": "..."}
# 2. HTTP Request 1: GET Clearbit (company by domain)
# 3. HTTP Request 2: GET LinkedIn (decision maker by company)
# 4. Slack: post to #leads

# The first execution:
# Input: {"email": "alice@acme.com"}
# Clearbit: {"name": "Acme Corp", "employees": 50, "industry": "Logistics"}
# LinkedIn: {"name": "John Smith", "title": "VP Operations", "linkedin": "..."}
# Slack: "🚀 New lead: Acme Corp (50 employees). Decision maker: John Smith, VP Operations (https://linkedin.com/in/johnsmith)"

# Time saved: 5 minutes per lead → 30 seconds per lead
# Cost: $0.001 per lead (Clearbit + LinkedIn API)
# Volume: 200 leads/day → 17 hours saved/day, $0.20/day
```

## Production addendum

The first workflow question is the answer to "show me you can build in n8n." The 60-second script:

> "4 steps. Install n8n. Create a workflow. Add 3 nodes (Webhook → HTTP → Slack). Test each node in isolation; test the workflow end-to-end. The 3-node starter is the proof; the 10-minute build is the muscle memory. I test as I build; the bug is caught at the right layer. The wrong choice is to build the entire workflow and test at the end. The right choice is the 3 + 4 + test-as-you-build + the 10-minute checklist."

This is the difference between a candidate who says "I've used n8n" and a candidate who says "I build the first workflow in 10 minutes: 3 nodes, 4 steps, test-as-you-build, 4 common errors + fixes, the 10-minute checklist." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-applications/n8n/01-first-workflow.json` — the exported first workflow.
- **Reference implementation**: `course/hardcode/level-7-n8n/01-hello-world.json` — the canonical first workflow.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/15-low-code-platforms.md` — n8n as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/04-ai-data-analyst/` — the data analyst agent could use the HTTP Request node for the sandbox.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/10-low-code-platforms.md` — n8n as a system design choice.

## The 3 questions this lecture preps you for

1. **"Walk me through your first n8n workflow."** Answer: 3 nodes (Webhook → HTTP Request → Slack), 4 steps (install, create, add, test), test-as-you-build pattern. 10 minutes from `npx n8n` to a working workflow that posts to Slack. The 4 common errors + fixes: webhook 404, HTTP undefined, Slack credential missing, Slack channel not found.
2. **"What is the test-as-you-build pattern?"** Answer: the FDE tests each node in isolation before wiring them. Test the Webhook (send a curl), test the HTTP Request (execute node with sample data), test the Slack (execute node), then test the workflow end-to-end. The bug is caught at the right layer; the FDE doesn't have to debug a 30-node workflow.
3. **"What are the 3 things that go wrong on a first workflow?"** Answer: (1) webhook 404 (using `/webhook-test/` for production or vice versa), (2) HTTP Request `undefined` (reading `$json` before the Webhook has run), (3) Slack credential missing or channel not found. The fixes are documented in the 10-minute build checklist; the FDE has seen them all in the first 10 minutes.

## Read next

`L7-3-nodes-and-credentials.md` — the 1000+ nodes, the OAuth/API key setup, the credential redaction pattern. The FDE's reference for picking the right node + the right credential for the job.
