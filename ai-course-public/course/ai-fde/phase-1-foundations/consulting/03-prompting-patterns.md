# Lesson 03 — Prompting Patterns & APIs

> **The 4 patterns you need to know, in 30 minutes.** No code in this lesson — but every pattern links to the lesson-03/lesson-04 Python that uses it.

By the end of this lesson you know the 4 prompting patterns that cover ~95% of FDE work:

1. **System + user** — the "persona + task" pattern (lesson 04 uses this)
2. **Structured output (JSON mode)** — the "give me parseable data" pattern
3. **Few-shot examples** — the "show, don't tell" pattern
4. **Function calling / tool use** — the "let the model call my code" pattern

You have a cheatsheet, 3 prompt variants for the same task, and the ability to pick the right pattern in 5 seconds.

---

## 🎯 Outcome

You produce **one artifact**:

- `prompt-cheatsheet.md` — a 1-page markdown document with the 4 patterns, when to use each, and a worked example of each in the PacificFreight context.

When you finish, you can read any FDE brief and say "I would use pattern X" without thinking.

## 🧠 Mindset

There are dozens of "prompt engineering" tricks. Most of them are noise. The FDE's prompting discipline is:

> **Pick the simplest pattern that solves the problem. Add complexity only when the simpler pattern fails.**

The four patterns below cover almost everything. When a customer asks "how do I get the model to do X," the answer is almost always one of these four. The trick is not to know fancy tricks — it is to **not use fancy tricks** until you need to.

The four traps to avoid:

1. **The clever-prompt trap.** Spending 2 hours rewriting a prompt to get a 5% accuracy gain. The CS person is not going to notice. The model latency and cost matter more.
2. **The chain-of-thought trap.** Asking the model to "think step by step" when the task is simple. Adds latency and cost for no benefit.
3. **The mega-prompt trap.** Stuffing every example, every rule, every edge case into one 3000-token system prompt. The model gets confused. Smaller, focused prompts work better.
4. **The API-shape trap.** Treating OpenAI and Anthropic as if they had the same API. They don't. Lesson 03's `03-modern-ai-tooling.py` wraps both — that is the right level of abstraction.

## 🛠️ Practice — the 4 patterns

### Pattern 1 — System + user (the default)

**When to use:** any single-turn task where the model needs to know its role and the user's request.

**Shape:**

```python
result = complete(
    system=PERSONA_AND_RULES,   # 1-3 paragraphs
    user=THE_TASK_AND_INPUT,     # 1 paragraph
)
```

**Worked example — PacificFreight reply drafter:**

```python
system = f"""You are a customer-service assistant for PacificFreight Co.
You draft concise replies in our voice. Follow this style guide:

{style_guide_text}

You will be given a customer email and a shipment's current status.
Output ONLY the reply. No preamble, no quotes."""

user = f"""Customer email:
{email_body}

Shipment in tracker:
- ID: {shipment.id}
- Status: {shipment.status}
- Last event: {shipment.last_event}
- Action required: {shipment.next_action_required or "(none)"}

Draft the reply."""
```

**When to graduate from this pattern:**
- The model is producing wrong output despite clear instructions
- The task is too complex to describe in a system prompt
- You need parseable output (use Pattern 2)

### Pattern 2 — Structured output (JSON mode)

**When to use:** when you need to **parse** the model's output programmatically. "Extract the shipment ID" is the canonical FDE example.

**Shape:**

```python
result = complete(
    system="You extract shipment IDs from emails. Return JSON only.",
    user=email_body,
    response_format={"type": "json_object"},   # OpenAI-specific; Anthropic has its own way
)
parsed = json.loads(result.text)
shipment_id = parsed.get("shipment_id")
```

**Why this matters:** without JSON mode, you write a regex to extract the ID (which catches 80%, as in lesson 04's Phase 1 design). With JSON mode, the model returns parseable JSON, and your code is simpler — but you pay the model for every call. The FDE trade-off:

- **80% regex + 20% human review** is cheaper than 100% LLM calls.
- **100% LLM + JSON mode** is correct when the cost of a missed ID is high (e.g., refund processing).

For PacificFreight Phase 1, the regex approach is right (low cost of missing an ID; the CS person catches it). For Phase 2 (auto-creating shipments, calculating refunds), the JSON-mode approach is right.

**Worked example — extract customer intent:**

```python
system = """You classify inbound logistics emails. Return JSON with:
- intent: one of "status_inquiry", "address_change", "damage_report", "refund_request", "other"
- shipment_id: string or null
- urgency: "low" | "medium" | "high"
- summary: one-sentence summary
"""
user = email_body
result = complete(system=system, user=user, response_format={"type": "json_object"})
parsed = json.loads(result.text)
```

That gives you structured data you can route on. A real Phase 2 build for PacificFreight would do this for every inbound email, then route:
- `status_inquiry` → reply drafter
- `damage_report` → escalation queue
- `refund_request` → manager queue

### Pattern 3 — Few-shot examples

**When to use:** when the model's first attempt is "almost right" but consistently wrong in a specific way. Adding 2-3 examples fixes it in 90% of cases.

**Shape:**

```python
system = f"""You are a PacificFreight CS assistant. Examples:

Example 1:
Customer: "Where's PF-1001?"
Status: delivered
Reply: "Hi Aisha, your shipment PF-1001 was delivered on..."

Example 2:
Customer: "PF-1003 stuck at customs??"
Status: held_customs
Reply: "Hi Mei Lin, your shipment PF-1003 is currently held..."

Now draft a reply for:
Customer: {email}
Status: {status}"""
```

**When to graduate from this pattern:**
- The model still gets it wrong after 3-5 examples → the problem is the prompt, not the examples
- You find yourself adding 20+ examples → you have a real ML problem, not a prompting one (use fine-tuning, not more examples)

**FDE rule:** if you need more than 5 examples in a prompt, you have a different problem. The right answer is a real eval suite and a fine-tuned model, not a 4000-token prompt.

### Pattern 4 — Function calling / tool use

**When to use:** when the model needs to **call code** to do its job. The model emits a structured "I want to call get_shipment(PF-1003)" request, your code runs the function, returns the result, and the model writes the final answer.

**Shape (OpenAI):**

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_shipment",
            "description": "Look up a shipment by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "shipment_id": {"type": "string", "pattern": "^PF-\\d{4,5}$"},
                },
                "required": ["shipment_id"],
            },
        },
    },
]
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Where is PF-1003?"}],
    tools=tools,
)
tool_call = response.choices[0].message.tool_calls[0]
if tool_call.function.name == "get_shipment":
    args = json.loads(tool_call.function.arguments)
    shipment = load_shipment(args["shipment_id"])
    # ... feed result back to model for the final reply
```

**When to use it:** any time the model needs **real-time data** it doesn't have in its training (shipment status, account balance, current inventory). Function calling is the FDE's interface between the LLM and the customer's systems.

**When NOT to use it:**
- The data is small enough to put in the system prompt (PacificFreight's style guide: ~2KB, fine in the prompt)
- The task is single-turn (just generate text, no real-time lookup)
- You are in Phase 1 and the customer is not ready to give you API access (function calling requires the tool definitions, which require stable APIs)

For PacificFreight Phase 1, you **don't** need function calling — `load_shipment` is called by your code, not by the model. For Phase 2 (multi-step agent that does lookup + drafting + escalation routing), you would.

### Decision tree — which pattern to use

```
Is the task a single turn with a known input format?
  YES → Pattern 1 (System + user)
  NO ↓

Do you need to parse the output programmatically?
  YES → Pattern 2 (JSON mode)
  NO ↓

Is the model "almost right" but consistently wrong in a specific way?
  YES → Pattern 3 (Few-shot)
  NO ↓

Does the model need to call your code (real-time data)?
  YES → Pattern 4 (Function calling)
  NO → Pattern 1 (you're overthinking it)
```

### 3 prompt variants for the same task — PacificFreight reply drafter

Same task, three patterns:

**Variant A — Pattern 1, system + user (the one lesson 04 uses):**

```python
system = "You are PacificFreight's CS assistant. Follow the style guide. Reply in the customer's language. Output ONLY the reply."
user = f"Email: {email}\nShipment: {shipment}"
```

**Variant B — Pattern 1 + 2 (system + JSON output for routing):**

```python
system = """You are PacificFreight's CS assistant. Output JSON with:
- "draft": the reply text
- "escalate": boolean (true if this needs a manager)
- "language": ISO code of the customer's language
- "intent": "status" | "damage" | "refund" | "other"
"""
user = f"Email: {email}\nShipment: {shipment}"
result = complete(system=system, user=user, response_format={"type": "json_object"})
```

**Variant C — Pattern 1 + 3 (system + 2 examples):**

```python
system = """You are PacificFreight's CS assistant. Examples:

Example 1:
Email: "Where's my package?"
Shipment: PF-1001, delivered
Draft: "Hi Aisha, your shipment PF-1001 was delivered on..."

Example 2:
Email: "PF-1003 stuck at customs??"
Shipment: PF-1003, held_customs
Draft: "Hi Mei Lin, your shipment PF-1003 is held at..."

Now draft for:
Email: {email}
Shipment: {shipment}"""
```

When to use which:
- **A** is the default. Use it for 80% of cases.
- **B** is right when you need to *route* the reply (escalate? tag for analytics?).
- **C** is right when A is producing wrong output in a specific, consistent way.

## 🏛️ FDE Lens — the technical reality underneath

The four patterns map directly to API features:

| Pattern | OpenAI | Anthropic | Cost | Latency |
|---|---|---|---|---|
| 1 (System + user) | `messages=[{role, content}]` | `system + messages` | Lowest | Fastest |
| 2 (JSON mode) | `response_format={"type": "json_object"}` | Use system prompt + parser | ~1.2x | ~1.2x |
| 3 (Few-shot) | Same as 1, longer prompt | Same | ~2-5x | ~1.5x |
| 4 (Function calling) | `tools=[...]` | `tools=[...]` | Variable | Slower (multi-turn) |

When the customer asks "is this expensive?", the answer is "depends which pattern." Pattern 1 is the cheapest. Pattern 4 is the most expensive. Lesson 03's `03-modern-ai-tooling.py` uses Pattern 1, with the cost tracking that lets you see the difference.

## 🌙 Reflect

Write 3-5 sentences:

1. Why is Pattern 1 the default? When would you skip it and go straight to Pattern 2 or 3?
2. The decision tree says "NO → Pattern 1 (you're overthinking it)" at the end. When is overthinking the right thing?
3. Few-shot examples add cost. What's the smallest number of examples that usually fixes a "consistently wrong in this specific way" bug?
4. Pattern 4 (function calling) requires you to give the model a tool definition. What is the FDE risk of giving the model a "send_email" tool? When would you do it anyway?

**What's next** — Lesson 04 uses **Pattern 1 (system + user)** to build the 1-pager for PacificFreight — the deliverable that ties all the consulting lessons together. The 1-pager is what you hand to the customer at the end of week 1; it is also what you hand to your own team at the start of week 2 to align on scope.
