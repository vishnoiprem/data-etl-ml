# Lesson 1: The ROI Formula for AI Agents

> **Before you write a single line of agent code, know if the math works.**
> 15 min. Code: `python3 lessons/01-roi-formula.py` (no API keys, pure math).

---

## 🎯 Architect Level

- 🟢 **Junior** (0-2 yr): I can run a single-agent demo end-to-end.
- 🟡 **Mid** (2-5 yr): I can pick the right tool registry + cost tracker for a use case.
- 🟠 **Senior** (5-8 yr): I can score a use case against the 4 criteria and budget a 6-month build.
- 🔴 **Staff** (8+ yr): I can defend a deployment decision with a 1000-cycle sensitivity analysis.

> **Picking the right level:** This lesson is for everyone. The formula in Section 2 is the same at every level — but only Staff-level readers will run the 1000-cycle review and read the P05 downside before saying "yes, deploy."

---

## 🧠 Concept (5 min)

Every AI agent deployment has **6 numbers**: 5 inputs (how much time, how much it's worth, how many tasks, how often it's used, how often it's right) and 1 cost (how much the LLM + infra costs per month). The 4 use case criteria (repetitive, language-heavy, tool-using, measurable) tell you **which problems are even worth estimating**. The formula then tells you **what the answer is in dollars per month**.

The wrong choice is to skip the formula and just build. The right choice is to estimate the 6 numbers first, run them through `monthly_roi()`, and only then open your editor.

**The formula (in code):**

```python
monthly_value = hours_saved_per_week * hourly_rate_usd * 4.33 * (volume_factor / 100) * adoption_rate * success_rate
monthly_roi   = monthly_value - agent_cost_usd
```

That's the whole course in 2 lines.

---

## 🛠️ Build It (45 min)

### Spec

Build a CLI tool that, given the 5 inputs and the cost, prints:
1. The 4 use case criteria score for 5 example workflows
2. The monthly ROI for 3 worked examples
3. The 5 input ranges the 1000-cycle review uses

### Acceptance Criteria

**Functional:**
- [ ] `python3 lessons/01-roi-formula.py` exits 0 with no args
- [ ] The 4-criteria score for the 5 example use cases prints as `PASS/FAIL (score N/4)`
- [ ] The 3 worked examples each print `ROI $X/mo ($X/yr)`

**Quality:**
- [ ] No external API calls
- [ ] Same input -> same output (deterministic)
- [ ] No magic numbers inside functions; all constants in the `# CONFIG` block

**Observability (Mid+):**
- [ ] Each section prints with a `-----` separator
- [ ] The demo prints a `=====` banner with the lesson number

### Starter Code

See `lessons/01-roi-formula.py` — the file is the starter code, fully runnable.

### Solution

The file IS the solution. Run it, read the output, change the 3 worked examples, re-run.

---

## 🏛️ Architect Notes

### Trade-offs

| Choice | Pros | Cons | Pick when |
|---|---|---|---|
| Run 1 trial per use case | Fast, easy | One bad draw can mislead you | Quick gut check |
| Run 1000 trials (this course) | See the distribution; P05 downside matters | 30 sec compute | You deploy with real money |
| Run 10,000 trials | Even tighter P05 | 5 min compute, marginal gain | Pre-IPO due diligence |
| Run with real measurement data | Ground truth | You don't have it yet (that's why we're estimating) | 3+ months post-launch |

### Capacity Model

| Knob | Range used in 1000-cycle | Why this range |
|---|---|---|
| `hours_saved_per_week` | 1.0 - 5.0 | A solo SMB owner can't free up more than ~5 hr/wk from one task |
| `hourly_rate_usd` | $25 - $150 | SGD 35 - 200 / hr equivalent; covers junior to senior operators |
| `volume_factor` | 10 - 100 | A weekly task count, not daily |
| `adoption_rate` | 50% - 100% | First month is 50%, mature agents hit 100% |
| `success_rate` | 70% - 100% | Below 70% the user abandons the agent |
| `agent_cost_usd` | $10 - $100/mo | Covers LLM API ($10-30) + observability + retries ($30-70) |

### Cost Model

| Component | Typical monthly cost (USD) | Why |
|---|---:|---|
| LLM API (gpt-4o-mini class) | $10 - $30 | ~1M tokens/wk for 100 tasks/wk |
| Observability (Langfuse, Helicone) | $0 - $30 | Free tier covers <10K traces/mo |
| Retries + idempotency storage | $0 - $10 | Postgres + a queue |
| Vector DB (if RAG) | $0 - $25 | pgvector is free; Pinecone is $25 |
| **Total** | **$10 - $100/mo** | Stay in this range for a healthy P05 |

### When NOT to use this lab's content

- **Don't** use this formula for a 1-shot creative task (e.g. "write me a wedding toast"). It fails the `repetitive` criterion.
- **Don't** use it for a task where the success rate is below 70% — the math will say positive ROI, but the user will churn.
- **Don't** use it for tasks where the hourly rate is "free" (e.g. a hobby project). The rate is a stand-in for *opportunity cost*, not literal wages.
- **Do** use it for any task that hits all 4 criteria and you can put a $/hr on your time.

### Production Checklist

- [ ] Run the 1000-cycle review with **your** estimated input ranges (not the defaults)
- [ ] Re-run after every change to the agent (prompt, tool, model)
- [ ] Compare the new `latest.json` to the old one; alert on `pct_positive` drop > 5%
- [ ] Set up a monthly cron: re-estimate the 5 inputs from your own usage data

---

## 🏗️ FDE Production Hardening (the patterns beyond this lab)

1. **The 4 use case criteria are a filter, not a goal.** If a use case fails 1 criterion, fix the process so it passes — don't lower the bar. ("Make it measurable" is a design constraint, not a wish.)

2. **The adoption rate is the silent killer.** A perfect agent with 0% adoption is a $0 agent. Measure adoption weekly, not monthly.

3. **The success rate has a non-linear effect on ROI.** A drop from 95% to 85% success cuts value by 11%. A drop from 80% to 70% cuts value by 14%. The slope steepens.

4. **Cost ceiling first, then quality.** Cap the agent at $X/mo. THEN make it as good as possible within that cap. The wrong order is to build a perfect agent and discover it costs $500/mo.

5. **The P05 is what you should quote your boss.** Mean ROI is for marketing. P05 is for budgeting. "In the worst 5% of cases, we still net $+X/mo" is the sentence that gets a project funded.

---

## 🌙 Reflect (10 min)

1. Pick one task you do every week. Score it against the 4 criteria. Did it pass?
2. Estimate the 5 inputs (hours, rate, volume, adoption, success) for that task. Be honest about adoption — most people overestimate.
3. Run `python3 code/run_1000_cycles.py` with the defaults. Read `results/latest.json`. Is the P50 positive? Is the P05 acceptable?
4. If the P50 is negative: which knob is most off? Adjust one input at a time and re-run. Which one moves the needle the most?

---

## References

- [LangChain: How to estimate LLM costs](https://python.langchain.com/docs/how_to/llm_token_usage_tracking/)
- [Anthropic: Prompt engineering for tool use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Langfuse observability pricing](https://langfuse.com/pricing)
- Course material: `course/ai-fde/.../intro-to-ai-agents/s09-ai-agents-in-business/L9-1-the-business-case-for-ai-agents.md`

### Reference implementation

The full 1000-cycle proof is in `../results/1000_cycle_review_*.md` and `../results/latest.json`. The executable version is in `../notebook.ipynb`.

---

*Last updated: 2026-10-14*
*License: MIT*
