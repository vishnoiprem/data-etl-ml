# L7.4: The AI Agent node — the 7 ingredients as a single drag-and-drop

> **FDE framing in one line:** the AI Agent node is n8n's implementation of the 7-ingredient agent from Section 2. Drag it onto the canvas, configure the model + system prompt + tools + memory, and the agent is alive. The FDE who can configure an AI Agent node in 10 minutes is the FDE who can ship an SMB agent in a day.

## The 3 things you'll learn

1. The 7 fields of the AI Agent node: model, system message, prompt, tools, memory, max iterations, output parser. Each field maps to a Section 2 ingredient; the FDE configures all 7 to ship the agent.
2. The 3 model selector options: OpenAI (GPT-5, GPT-5-mini), Anthropic (Claude Sonnet 4.5, Claude Haiku 4.5), Ollama (local models). The model selector is the cost-quality dial.
3. The "tools as nodes" pattern: every tool the agent can call is a separate node wired to the AI Agent node. The agent decides which tool to call based on the prompt; n8n executes the tool. The pattern is the same as Section 2.2, but visual.

## Concept

The AI Agent node is n8n's first-class implementation of the 7-ingredient agent. The FDE drags the AI Agent node onto the canvas, configures 7 fields (model, system message, prompt, tools, memory, max iterations, output parser), and the agent is alive. The node handles the loop driver, the cost ceiling, the audit log, and the error recovery — the FDE configures the behavior. **The AI Agent node is the 200-line `SingleAgent` class from Section 6.2, but in a visual form.**

The 7 fields of the AI Agent node:

1. **Model.** The LLM the agent calls. The FDE picks from OpenAI (gpt-5, gpt-5-mini, gpt-4.1, gpt-4.1-mini), Anthropic (claude-sonnet-4.5, claude-haiku-4.5), Ollama (local models like qwen2.5:1.5b), Groq, Cohere, and more. The model is the cost-quality dial: gpt-5-mini for routine steps, gpt-5 for hard steps.
2. **System Message.** The system prompt. The FDE writes a 5-section system prompt (role, tools, output format, guardrails, examples) per Section 2.5. The system message is the agent's contract with the model; the FDE iterates on the system message to tune the behavior.
3. **Prompt (User Message).** The input. The prompt can be a fixed string, a reference to `$json`, or a reference to an earlier node's output. The FDE templates the prompt with `{{$json.email}}` to pass the trigger's input to the agent.
4. **Tools.** The functions the agent can call. Each tool is a separate node wired to the AI Agent node. The AI Agent node sees a list of "tool descriptions" (name, description, parameters); the model decides which tool to call; n8n executes the tool and returns the result. The pattern is the same as Section 2.2.
5. **Memory.** The conversation history. The FDE picks from Window Buffer Memory (last N messages), Postgres Chat Memory (persistent), Redis Chat Memory, or a custom memory node. The memory is the agent's context across turns.
6. **Max Iterations.** The loop ceiling. Default: 30. The FDE lowers it to 10 for cost-sensitive workflows; raises it to 50 for research workflows. The max iterations is the loop detector (Section 6.5).
7. **Output Parser.** The structured output. The FDE can leave it as plain text, or configure an "Auto-fixing Output Parser" that parses the model output into a JSON schema. The output parser is the Section 2.6 pattern.

The 3 model selector options:

1. **OpenAI.** GPT-5, GPT-5-mini, GPT-4.1, GPT-4.1-mini, o1, o3-mini. The right choice for general-purpose agents; the right choice for code generation; the right choice when the customer has an OpenAI contract.
2. **Anthropic.** Claude Sonnet 4.5, Claude Haiku 4.5, Claude Opus 4.5. The right choice for long-context agents (200K tokens); the right choice for nuanced reasoning; the right choice when the customer has an Anthropic contract.
3. **Ollama.** Local models: qwen2.5:1.5b, llama-3.3:70b, mistral:7b. The right choice for cost-sensitive workflows; the right choice for data-sensitive workflows (the data never leaves the network); the right choice for the SLM-distilled drafter from Phase 4 Project 3.

The "tools as nodes" pattern is the visual expression of the function-calling protocol from Section 2.2. Every tool the agent can call is a separate node on the canvas, wired to the AI Agent node. The agent emits a `tool_call` (e.g., `{"name": "tracker.lookup", "args": {"shipment_id": "PF-1003"}}`); n8n routes the call to the corresponding tool node; the tool node executes; the result is fed back to the agent. **The pattern is identical to Section 2.2; the difference is that the FDE does not write the JSON contract — n8n does.**

## The pattern

The AI Agent node with 3 tools (the canonical setup):

```
                    ┌─────────────────────┐
                    │     AI Agent        │
┌──────────┐        │  ┌───────────────┐  │        ┌──────────┐
│ Webhook  │───────▶│  │ Model: gpt-5  │  │───────▶│  Slack   │
│ Trigger  │        │  │ System: ...   │  │        │ (output) │
└──────────┘        │  │ Tools: [T1,T2]│  │        └──────────┘
                    │  │ Memory: ...   │  │
                    │  │ Max iter: 10  │  │
                    │  └───────────────┘  │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Tool 1:  │    │ Tool 2:  │    │ Tool 3:  │
        │  HTTP    │    │ Postgres │    │   Set    │
        │ (lookup) │    │ (query)  │    │ (filter) │
        └──────────┘    └──────────┘    └──────────┘
```

The AI Agent node configuration (the 7 fields):

```json
{
  "name": "Lead Qualification Agent",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "model": "gpt-5-mini",
    "systemMessage": "You are a lead qualification agent for Northwind Logistics, a Singapore-Vietnam cross-border freight broker.\n\nYour goal: qualify inbound leads by (1) enriching the company data, (2) checking lane coverage, (3) scoring the lead on a 0-100 scale.\n\nTools:\n- clearbit_lookup: Get company info (employees, industry, revenue)\n- lane_check: Check if the customer's desired lane is supported\n- hubspot_search: Check if the lead is already in HubSpot\n\nOutput format: Return a JSON object with {qualified: bool, score: int, reason: str}.\n\nGuardrails:\n- Never make a tool call without first reading the lead's email\n- Never score a lead above 80 without checking lane coverage\n- If the email is from a free email provider (gmail, yahoo), score 0\n\nExamples:\nInput: alice@acme.com (acme.com domain)\nOutput: {\"qualified\": true, \"score\": 75, \"reason\": \"Mid-size logistics company, lane supported\"}",
    "prompt": "={{$json.email}}",
    "tools": [
      {"node": "Clearbit Lookup", "type": "@n8n/n8n-nodes-langchain.toolHttpRequest"},
      {"node": "Lane Check", "type": "@n8n/n8n-nodes-langchain.toolPostgres"},
      {"node": "HubSpot Search", "type": "@n8n/n8n-nodes-langchain.toolHttpRequest"}
    ],
    "memory": {
      "type": "windowBuffer",
      "contextWindowLength": 10,
      "sessionId": "={{$execution.id}}"
    },
    "maxIterations": 10,
    "outputParser": {
      "type": "autoFixing",
      "schema": "{\"type\": \"object\", \"properties\": {\"qualified\": {\"type\": \"boolean\"}, \"score\": {\"type\": \"integer\"}, \"reason\": {\"type\": \"string\"}}}"
    }
  },
  "position": [500, 300]
}
```

The 3 model options compared (the cost-quality dial):

```python
MODEL_OPTIONS = {
    "gpt-5-mini": {
        "input_cost_per_1m": 0.15,
        "output_cost_per_1m": 0.60,
        "context_window": 128_000,
        "best_for": "Routine steps, classification, simple extraction",
        "n8n_use_case": "Lead scoring, email triage, simple Q&A",
    },
    "gpt-5": {
        "input_cost_per_1m": 2.50,
        "output_cost_per_1m": 10.00,
        "context_window": 128_000,
        "best_for": "Hard reasoning, planning, complex tool use",
        "n8n_use_case": "Multi-step research, code generation, planning",
    },
    "claude-sonnet-4.5": {
        "input_cost_per_1m": 3.00,
        "output_cost_per_1m": 15.00,
        "context_window": 200_000,
        "best_for": "Long-context, nuanced reasoning, document analysis",
        "n8n_use_case": "Contract review, long-email analysis, multi-doc RAG",
    },
    "claude-haiku-4.5": {
        "input_cost_per_1m": 0.80,
        "output_cost_per_1m": 4.00,
        "context_window": 200_000,
        "best_for": "Long-context at moderate cost, simple extraction",
        "n8n_use_case": "Email classification, simple Q&A with long docs",
    },
    "qwen2.5:1.5b (Ollama)": {
        "input_cost_per_1m": 0.00,
        "output_cost_per_1m": 0.00,
        "context_window": 32_000,
        "best_for": "Cost-sensitive workflows, data-sensitive workflows",
        "n8n_use_case": "The SLM-distilled drafter from Phase 4 Project 3",
    },
}
```

The "tools as nodes" pattern in detail (3 tools, 1 agent):

```python
TOOL_NODES = [
    {
        "name": "Clearbit Lookup",
        "type": "toolHttpRequest",
        "description": "Look up a company by domain. Use this to get company size, industry, and revenue.",
        "parameters": {
            "method": "GET",
            "url": "=https://company.clearbit.com/v2/companies/find?domain={{$json.email.split('@')[1]}}",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "clearbitApi",
        },
        "schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "The lead's email address"}
            },
            "required": ["email"]
        }
    },
    {
        "name": "Lane Check",
        "type": "toolPostgres",
        "description": "Check if a lane is supported. Use this to verify the customer's desired shipping lane.",
        "parameters": {
            "operation": "executeQuery",
            "query": "=SELECT supported FROM lanes WHERE origin = '{{$json.origin}}' AND destination = '{{$json.destination}}'",
        },
        "schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Origin country code (e.g., SG)"},
                "destination": {"type": "string", "description": "Destination country code (e.g., VN)"}
            },
            "required": ["origin", "destination"]
        }
    },
    {
        "name": "HubSpot Search",
        "type": "toolHttpRequest",
        "description": "Search HubSpot for an existing contact. Use this to check if the lead is already in the CRM.",
        "parameters": {
            "method": "GET",
            "url": "=https://api.hubapi.com/crm/v3/objects/contacts/search",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "hubspotApi",
            "body": {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": "={{$json.email}}"
                    }]
                }]
            }
        },
        "schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "The lead's email address"}
            },
            "required": ["email"]
        }
    },
]
```

The pattern that wins interviews is the "7 fields + 3 model options + tools as nodes" pattern. The candidate who says "I configure 7 fields on the AI Agent node: model, system message, prompt, tools, memory, max iterations, output parser. Each maps to a Section 2 ingredient. The 3 model options are OpenAI, Anthropic, Ollama. The tools are separate nodes; the agent decides which to call; n8n executes. The wrong choice is to build the agent in raw Python when n8n is the right tool. The right choice is the 7 fields + 3 options + tools as nodes" is the candidate who demonstrates the n8n-agent-mindset.

## Code or example

The system prompt template (5 sections, the FDE's reference):

```markdown
# Lead Qualification Agent — System Prompt

## Role
You are a lead qualification agent for Northwind Logistics, a Singapore-Vietnam
cross-border freight broker. You qualify inbound leads by enriching company data,
checking lane coverage, and scoring the lead on a 0-100 scale.

## Tools
- `clearbit_lookup(email)`: Get company info (employees, industry, revenue)
- `lane_check(origin, destination)`: Check if a shipping lane is supported
- `hubspot_search(email)`: Check if the lead is already in HubSpot

## Output Format
Return a JSON object with this exact structure:
{
  "qualified": true | false,
  "score": 0-100,
  "reason": "string (max 200 chars)"
}

## Guardrails
- Never make a tool call without first reading the lead's email
- Never score a lead above 80 without verifying lane coverage
- If the email is from a free email provider (gmail.com, yahoo.com, hotmail.com),
  return {"qualified": false, "score": 0, "reason": "Free email provider"}
- If the company has fewer than 10 employees, return {"qualified": false, "score": 20, "reason": "Too small"}

## Examples

### Example 1: Mid-size qualified lead
Input: alice@acme.com
Tool calls: clearbit_lookup → lane_check(SG, VN) → hubspot_search
Output: {"qualified": true, "score": 75, "reason": "Mid-size logistics company, SG-VN lane supported"}

### Example 2: Free email provider
Input: bob@gmail.com
Tool calls: (none)
Output: {"qualified": false, "score": 0, "reason": "Free email provider"}

### Example 3: Lane not supported
Input: carol@bigcompany.com
Tool calls: clearbit_lookup → lane_check(US, MX)
Output: {"qualified": false, "score": 40, "reason": "Lane US-MX not supported; only SG-VN"}
```

The memory options (the 3 patterns):

```python
MEMORY_OPTIONS = {
    "window_buffer": {
        "description": "Last N messages; in-memory; lost on workflow restart",
        "config": "contextWindowLength: 10 (default)",
        "best_for": "Stateless workflows; single-execution conversations",
        "cost": "Free (in-memory)",
    },
    "postgres_chat_memory": {
        "description": "Last N messages; persisted in Postgres; survives restarts",
        "config": "tableName: 'n8n_chat_memory'; contextWindowLength: 50",
        "best_for": "Multi-session conversations; long-running workflows",
        "cost": "1 row per message; minimal storage",
    },
    "redis_chat_memory": {
        "description": "Last N messages; persisted in Redis with TTL; fast access",
        "config": "keyPrefix: 'n8n:memory:'; ttl: 86400 (24 hours)",
        "best_for": "High-throughput workflows; time-limited conversations",
        "cost": "1 key per session; minimal storage",
    },
}
```

The AI Agent node execution log (the FDE's debugger):

```json
{
  "node": "Lead Qualification Agent",
  "input": {"email": "alice@acme.com"},
  "execution": {
    "iterations": 3,
    "tool_calls": [
      {
        "iteration": 1,
        "tool": "clearbit_lookup",
        "args": {"email": "alice@acme.com"},
        "result": {"name": "Acme Corp", "employees": 50, "industry": "Logistics"}
      },
      {
        "iteration": 2,
        "tool": "lane_check",
        "args": {"origin": "SG", "destination": "VN"},
        "result": {"supported": true}
      },
      {
        "iteration": 3,
        "tool": "hubspot_search",
        "args": {"email": "alice@acme.com"},
        "result": {"found": false}
      }
    ],
    "model_calls": [
      {
        "iteration": 1,
        "model": "gpt-5-mini",
        "input_tokens": 412,
        "output_tokens": 89,
        "cost_usd": 0.0002
      },
      {
        "iteration": 2,
        "model": "gpt-5-mini",
        "input_tokens": 523,
        "output_tokens": 67,
        "cost_usd": 0.0002
      },
      {
        "iteration": 3,
        "model": "gpt-5-mini",
        "input_tokens": 634,
        "output_tokens": 45,
        "cost_usd": 0.0002
      },
      {
        "iteration": 4,
        "model": "gpt-5-mini",
        "input_tokens": 745,
        "output_tokens": 23,
        "cost_usd": 0.0001
      }
    ],
    "total_cost_usd": 0.0007,
    "duration_ms": 2340
  },
  "output": {
    "qualified": true,
    "score": 75,
    "reason": "Mid-size logistics company, SG-VN lane supported"
  }
}
```

## Production addendum

The AI Agent node question is the answer to "how do you build an agent in n8n." The 60-second script:

> "7 fields on the AI Agent node: model (OpenAI, Anthropic, Ollama), system message (5-section prompt), prompt (the input), tools (separate nodes), memory (window, Postgres, Redis), max iterations (loop detector), output parser (structured output). Each maps to a Section 2 ingredient. The tools are separate nodes; the agent decides which to call; n8n executes. The wrong choice is to build the agent in raw Python when n8n is the right tool. The right choice is the 7 fields + 3 model options + tools as nodes + the 5-section system prompt."

This is the difference between a candidate who says "I built an agent in n8n" and a candidate who says "7 fields, 3 model options, tools as nodes, 5-section system prompt, 3 memory options, the execution log is the debugger." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-applications/n8n/03-ai-agent.json` — the AI Agent node example.
- **Reference implementation**: `course/hardcode/level-7-n8n/03-ai-agent.md` — the canonical AI Agent setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/15-low-code-platforms.md` — n8n as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/01-mcp-drafter/` — the MCP server's tool definitions parallel the n8n tool nodes.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/10-low-code-platforms.md` — n8n as a system design choice.

## The 3 questions this lecture preps you for

1. **"How do you build an agent in n8n?"** Answer: drag the AI Agent node, configure 7 fields (model, system message, prompt, tools, memory, max iterations, output parser), wire 3+ tool nodes, test. The tools are separate nodes; the agent decides which to call; n8n executes. The pattern is the same as Section 2; the implementation is visual.
2. **"What are the 3 model options?"** Answer: OpenAI (gpt-5, gpt-5-mini), Anthropic (claude-sonnet-4.5, claude-haiku-4.5), Ollama (local models like qwen2.5:1.5b). The model is the cost-quality dial. The right choice is gpt-5-mini for routine steps, gpt-5 for hard steps, claude-sonnet-4.5 for long context, ollama for cost-sensitive.
3. **"What is the 'tools as nodes' pattern?"** Answer: every tool the agent can call is a separate node wired to the AI Agent node. The agent sees a list of tool descriptions; the model emits a tool_call; n8n routes to the corresponding tool node; the tool executes; the result feeds back. The pattern is identical to Section 2.2; the FDE does not write the JSON contract.

## Read next

`L7-5-vector-store-and-memory.md` — the vector store nodes (Qdrant, Pinecone, Postgres pgvector), the simple vs window memory, the RAG pattern in n8n.
