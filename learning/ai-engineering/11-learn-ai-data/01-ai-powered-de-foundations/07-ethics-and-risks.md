# Lesson 7 — Ethics & Risks

> **Type:** Article · Module 1 · AI-Powered DE Foundations
> The risks you cannot delegate to AI: PII, hallucination, bias, IP, vendor lock-in, and the ethics of automating decisions.

---

## Why this lesson exists

The productivity gains from AI are real. The risks are also real. The risks don't disappear because the productivity is good — they compound. As a DE in 2026, you own the **data layer** of every AI product that touches your warehouse. That means you own most of these risks whether you like it or not.

```
              RISK SURFACE FOR A DE USING AI IN 2026

   [your repo]   ──►  AI vendor (Cursor, Copilot, Claude Code)
   [your schema] ──►  AI vendor (training, telemetry, fine-tuning)
   [your prompts]──►  may contain PII if you're not careful
   [your outputs]──►  may contain hallucinated facts about YOUR data
   [your users]  ──►  affected by AI-generated pipelines that ship wrong
   [your org]    ──►  affected by IP / license / compliance issues
```

---

## Risk 1 — Data exfiltration via prompts

### What it looks like
You paste your schema into a prompt to get better SQL output. The schema has a customer PII sample. The vendor logs it, indexes it, or (in the worst case) trains on it.

### What to do
1. **Read every vendor's data-retention policy.** Cursor, Copilot, Claude Code, Aider — all different.
2. **Turn off telemetry / training opt-in.** Most vendors default to "on" for product improvement.
3. **Never paste raw PII into a prompt.** Use schema names only. If you need sample values, use synthetic or redacted values.
4. **Self-host where the policy is unacceptable.** Aider runs locally. vLLM + your own model is another option.
5. **Maintain a `data-classification.md`** that labels which columns/tables can be shared with AI tools.

```markdown
# data-classification.md

| Class | Examples | AI-tool allowed? |
|---|---|---|
| Public | `dim_region`, public schema docs | Yes |
| Internal | `fct_orders` (no PII) | Yes, no opt-out |
| Confidential | `dim_user.email`, `fct_orders.user_id` | Aggregated only |
| Restricted | `dim_user.ssn`, raw PII | **No AI tooling** |
```

---

## Risk 2 — Hallucinated facts about your data

### What it looks like
The AI confidently tells you *"your `dim_user` table has a `lifetime_value` column"*. It doesn't. You build a model on the hallucinated column, prod breaks.

### What to do
- **Treat every claim about YOUR data as suspect.** Verify against your actual schema, every time.
- **Use warehouse MCP for live schema reads.** The AI queries the real catalog, not its memory.
- **Pin the model version.** Behavior drift across versions is real.

---

## Risk 3 — Plausible-but-wrong output (the silent killer)

### What it looks like
The AI writes a query that returns a number. The number looks reasonable. The dashboard goes to the CEO. The CEO makes a decision based on a query that joined on the wrong column.

This is the worst failure mode because **no alert fires**. Everything looks fine.

### What to do
1. **Verification habits** (Lesson 5) are the entire defense.
2. **Pair every AI-generated metric with a hand-written sanity check.**
3. **For exec-facing dashboards, the number must be reproducible by a second person from scratch.** If you can't reproduce it, the dashboard is suspect.

---

## Risk 4 — Bias in AI-generated decisions

### What it looks like
You use an LLM to label customer support tickets for routing. The LLM under-routes Spanish-language tickets because its training data skewed English. Customers in Spanish-speaking markets get worse support.

### What to do
- **Audit any AI-driven decision for subgroup performance.** Not just overall accuracy — accuracy *by slice*.
- **For high-stakes decisions (credit, healthcare, hiring, fraud), keep a human in the loop.** This is a legal requirement in many jurisdictions.
- **Document the audit.** If you can't show your work, you can't defend the decision.

---

## Risk 5 — IP and licensing

### What it looks like
The AI suggests code from an open-source library with a license that conflicts with your commercial product. Or it reproduces a snippet from a copyrighted source verbatim.

### What to do
- **Most modern LLMs have been trained to not reproduce copyrighted code verbatim**, but the guarantee is not absolute.
- **Use a license-checker** in CI (FOSSA, Snyk, etc.) regardless of whether AI wrote the code.
- **For high-IP codebases, run inference locally** with a self-hosted model trained only on permitted data.

---

## Risk 6 — Model-supply risk

### What it looks like
You build your pipeline on GPT-5 in January. OpenAI deprecates it in June. Or Anthropic changes Claude's behavior in a way that breaks your prompts. Or your vendor has a multi-day outage.

### What to do
- **Avoid vendor lock-in at the prompt layer.** Wrap LLM calls behind an interface you control.
- **Cache responses** where determinism matters.
- **Have a fallback model** for critical paths.
- **Pin versions.** Update deliberately.

```python
# Bad
response = openai.ChatCompletion.create(model="gpt-5", ...)

# Better
response = llm_client.complete(
    model=os.environ["LLM_MODEL"],   # pinned in deploy config
    messages=...,
)
```

---

## Risk 7 — The ethics of automating decisions

### What it looks like
A team uses an LLM to decide which customers get a refund. The LLM denies 30% of legitimate refunds. Customers churn. The team didn't build an appeal path because "it's just an AI."

### What to do
- **AI decisions that affect people need an appeal path.** Period.
- **The DPO/legal/compliance team must be in the loop before any AI touches a customer-facing decision.**
- **Document the decision flow.** "The AI decides X; the human can override Y" must be visible to anyone affected.
- **For GDPR / CCPA / equivalent, the right to explanation applies.** If you can't explain the decision, you can't ship it.

---

## Risk 8 — Energy and environmental cost

### What it looks like
Training and running large models consumes significant energy. A team routes 100 M trivial classification calls through a frontier model when a small model (or no model) would have worked.

### What to do
- **Match the model to the task.** A 7B parameter model handles 80% of classification tasks. Use a frontier model only when the task demands it.
- **Cache aggressively.** Most prompts are repeated in slightly different forms.
- **Track cost per task.** If your "AI summariser" costs $0.05 per call and you're making 10 M calls a day, you have a budget problem.

---

## A practical ethics checklist for every AI feature

Before shipping any AI-driven feature into production:

- [ ] **Data classification** — what data does the AI see? Is it within policy?
- [ ] **Vendor review** — what is the data-retention and training policy?
- [ ] **Bias audit** — performance across relevant subgroups
- [ ] **Appeal path** — humans can override, customers can dispute
- [ ] **Reproducibility** — second engineer can re-derive the output
- [ ] **Cost ceiling** — alerts on per-call or aggregate cost
- [ ] **Fallback** — what happens when the AI is down or wrong
- [ ] **Logging** — every call is logged with prompt + response + model version
- [ ] **Compliance sign-off** — DPO/legal has reviewed the use case
- [ ] **Decommissioning plan** — how do you turn this off cleanly if needed

---

## What Comes Next

> Lesson 8 — **Quiz: AI-Powered DE Foundations** — a self-check on the eight lessons of Module 1.
