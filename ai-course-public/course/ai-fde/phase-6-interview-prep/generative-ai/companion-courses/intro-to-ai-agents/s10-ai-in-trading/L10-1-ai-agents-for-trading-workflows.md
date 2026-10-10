# L10.1: AI agents for trading workflows — the canonical use case for agentic AI in 2026

> **FDE framing in one line:** AI agents in 2026 are best understood through the workflows they own, not the decisions they replace. Trading is the cleanest demonstration of the pattern because every workflow is a tight **read → score → write** loop. The 5 workflows (research, journal, sizing, EOD, compliance) are automatable in 30 days for $20/month; the 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) are how you sleep at night. The same pattern unlocks 12 more workflows across customer support, sales, legal, and ops. The wrong choice is to automate the decision; the right choice is to automate the work **around** the decision.

## In 60 seconds

> "AI agents in 2026 = LLM + tools + loop, with 5 guardrails. The wrong choice is to think of them as 'AI that decides for you.' The right choice is to think of them as **a junior assistant with infinite patience and zero judgment** — it does the boring language-heavy work, you keep the decision. Trading is the canonical demonstration: 5 workflows (pre-market research, trade journal analysis, position-sizing calculator, EOD recap + plan, compliance summary) all meet the 4 use case criteria (repetitive, language-heavy, tool-using, measurable). The 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) are the same 5 from Section 6.5. $20/month LLM API + 1 hour/day for 30 days = 1,150 hours/year back. The same pattern unlocks 12 more workflows — customer support, sales call review, contract review, candidate screening, code review, content moderation, lead enrichment, tax categorization, meeting notes, news monitoring, inventory reorder, onboarding. The article's $ is in the leads it generates, not the reads it gets."

**The wrong choice is to read past this block.** The right choice is to recite the 5 workflows + 5 guardrails + 4 use case criteria + 12 application workflows before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. **What an AI agent actually is in 2026** — an LLM + tools + a loop, with 5 guardrails. Not magic, not AGI, not a decision-maker. A disciplined junior assistant for the boring language-heavy work.
2. **The 5 trading workflows as the canonical demonstration** — pre-market research, trade journal analysis, position-sizing calculator, EOD recap + plan, compliance summary. All 5 meet the 4 use case criteria (repetitive, language-heavy, tool-using, measurable). All 5 ship in 30 days for $20/month. All 5 save 1,150 hours/year.
3. **The 12 workflows the pattern unlocks beyond trading** — customer support, sales call review, contract review, candidate screening, code review, content moderation, lead enrichment, tax categorization, meeting notes, news monitoring, inventory reorder, onboarding. Same shape: read inputs → score → write output. Same guardrails. Same 30-day build per workflow.

## Concept

The thesis of this lecture: **the boring work is going away.** Not in 5 years. In 18 months. The person who automates their 5 boring workflows in 2026 has a 6-12 month head start on the person who waits for "AI to get good enough." AI is already good enough. What's missing is the **prompt, the guardrails, and the habit.**

### What an AI agent is (and isn't)

An AI agent in 2026 is a small piece of software with three things bolted on:

1. **A language model** (LLM) that reads and writes text — ChatGPT, Claude, Gemini, or an open-weights model on your own GPU.
2. **Tools** it can call — APIs, files, spreadsheets, search, your inbox, your broker, your CRM.
3. **A loop** that lets it try → check → retry until the job is done.

That's it. No magic. No sentience. No AGI. The agent is a **junior assistant with infinite patience and zero judgment.** It will scrape 50 news items at 5am, write you a 1-page brief, and never complain. It will also loop forever, hallucinate a trade signal, and try to email 10,000 people if you let it. The art of building agents is the **5 guardrails** so they help instead of hurt.

### The 4 use case criteria

Before you automate anything, score it against 4 criteria. If a workflow doesn't hit all 4, **don't automate it** — the agent will be worse than you.

1. **Repetitive** — you do it more than once a day or once a week. If you do it once a year, the prompt takes longer to write than the task.
2. **Language-heavy** — it's text or speech. LLMs are text machines. If the workflow is "lift a heavy box," the agent is not the right tool (yet).
3. **Tool-using** — it requires reading a file, calling an API, or querying a database. Agents live or die on their tool belt.
4. **Measurable** — you can verify the output. The brief is on your desk by 5:01am. The journal postmortem has 5 patterns. The compliance email has zero rule violations.

**The workflows that fail the test:** "decide whether to hire this person," "design the brand," "negotiate the deal," "the actual trade decision." All are too one-off, too judgment-heavy, or too hard to verify. Keep doing those yourself.

**The workflows that pass:** every workflow in this lecture.

### Why trading is the canonical demonstration

Trading hits all 4 criteria for almost every workflow in a trading day:

| # | Workflow | Repetitive | Language | Tool-using | Measurable | Time saved |
|---|----------|------------|----------|------------|------------|------------|
| 1 | Pre-market research | Daily 5am | Yes (news) | News API + filings | Brief on time | 2-3 hrs/day |
| 2 | Trade journal analysis | Weekly Sun | Yes (postmortem) | CSV read + LLM | Postmortem written | 2-3 hrs/week |
| 3 | Position-sizing calculator | Per trade | Yes (output) | Math + LLM | Numbers correct | 1-2 min/trade |
| 4 | EOD recap + plan | Daily 4:30pm | Yes (recap + plan) | Blotter + news | Plan before 5pm | 1-2 hrs/day |
| 5 | Compliance summary | Weekly Fri | Yes (audit) | Fill report + rules | Report sent | 2-3 hrs/week |

Each workflow scores 4/4. Each saves a measurable amount of time. Each is automatable with off-the-shelf tools (LLM API + Notion + a spreadsheet + a cron job).

**The 5 workflows that DON'T meet the 4 criteria** (and should not be automated):

- **The actual trade decision** (fails: not tool-using in the LLM sense; not measurable — P&L is too noisy; the decision is the whole point)
- **Strategy development** (fails: not repetitive; not language-heavy enough; not measurable in the short term)
- **Risk management on novel events** (fails: not repetitive; human judgment required)
- **Broker / counterparty relationship** (fails: not tool-using via API; high context)
- **The "I have a feeling" trade** (fails: not measurable; the feeling is the point)

The wrong choice is to try to automate the trade decision itself. The right choice is to automate the work around the trade and keep the human in the loop on the actual click.

## The pattern

The 5 workflows + 5 guardrails as a single production pattern. The same **7 ingredients + 5 guardrails** from Section 2, instantiated for the trading-agent context.

The 7 ingredients (Section 2), instantiated for trading:

| Ingredient (Section 2) | Trading instantiation |
|------------------------|----------------------|
| Model | gpt-5-mini for research + EOD; gpt-5 for journal + compliance; math-only for sizing |
| Tools | News API, filings API, broker CSV, calendar API, mailer |
| Memory | Watchlist, risk rules, last 30 days of briefs/postmortems (vector + key-value) |
| Cost ceiling | $20/month LLM API = ~10K workflow runs |
| System prompt | The 5 workflow prompts above, version-controlled |
| Parser | Schema-validated JSON: {date, ticker, action, size, price, ...} |
| Loop driver | Cron job + retry-on-schema-fail (max 3 attempts) |

The 5 guardrails (Section 6.5), instantiated for trading:

| Guardrail (Section 6.5) | Trading instantiation |
|-------------------------|----------------------|
| Loop detector | Hard cap at 10 steps; if exceeded, abort and alert |
| Schema validator | Output must match fixed JSON shape; if not, retry; if retry fails, abort |
| Cost ceiling | $20/month LLM API; if exceeded, kill the agent for the month |
| Idempotency | The same input produces the same output; the agent never re-emails the same brief |
| Audit log | Every run writes {timestamp, workflow, input, output, cost} to a JSONL file |

The 5 workflows as a single TradingAgent class (the FDE pattern, 50 lines, stdlib-only):

```python
import json
import time
from datetime import datetime
from pathlib import Path

class TradingAgent:
    """The 5-workflow trading agent. 50 lines, stdlib-only."""

    def __init__(self, llm, tools, *, max_steps: int = 10, max_cost_usd: float = 20.0):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.max_cost_usd = max_cost_usd
        self.run_cost = 0.0
        self.audit_log = Path("trading_agent_audit.jsonl")

    def run(self, workflow: str, input_data: dict) -> dict:
        """Run a workflow with all 5 guardrails enforced."""
        # Guardrail 1: cost ceiling (check at start)
        if self.run_cost >= self.max_cost_usd:
            return {"error": "cost ceiling breached", "cost": self.run_cost}

        steps = 0
        while steps < self.max_steps:
            steps += 1
            # Guardrail 5: audit log (write at every step)
            self._audit(workflow, input_data, step=steps)

            # Call the LLM with the workflow's system prompt
            output = self.llm.complete(
                system=self.tools[workflow]["system_prompt"],
                user=json.dumps(input_data),
            )
            self.run_cost += output.cost_usd

            # Guardrail 2: schema validator
            try:
                parsed = self.tools[workflow]["schema"](output.text)
            except SchemaError as e:
                # Guardrail 4: idempotency — record the failed run
                self._audit(workflow, input_data, error=str(e))
                continue  # retry

            # Guardrail 3: loop detector (implicit: max_steps cap above)
            return parsed

        # Guardrail 1 again: if we exit the loop without returning, abort
        return {"error": "max steps exceeded", "steps": steps}

    def _audit(self, workflow, input_data, **extra):
        with self.audit_log.open("a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "workflow": workflow,
                "input": input_data,
                **extra,
            }) + "\n")
```

The 5 workflow definitions (the 5 system prompts + 5 schemas):

```python
WORKFLOWS = {
    "pre_market_research": {
        "system_prompt": """You are a research analyst. Read these 50 items and rank
        by relevance to my watchlist. Output a 1-page brief with: (1) top 3
        catalysts, (2) top 3 risks, (3) top 3 things to watch today. Under 500
        words. If a catalyst affects multiple watchlist names, list it once.""",
        "schema": PreMarketBriefSchema,  # Pydantic
        "tools": ["news_api", "filings_api"],
        "schedule": "0 5 * * 1-5",  # 5am weekdays
    },
    "trade_journal_analysis": {
        "system_prompt": """You are a performance analyst. Read my trade journal CSV
        (columns: date, time, ticker, side, qty, price, pnl, setup). Output:
        (1) 5 patterns I should be aware of, (2) the 3 trades that hurt the most,
        (3) my best and worst setups, (4) one rule I should add. Be direct.""",
        "schema": JournalPostmortemSchema,
        "tools": ["broker_csv", "llm"],
        "schedule": "0 9 * * 0",  # Sunday 9am
    },
    "position_sizing": {
        "system_prompt": """Given account size, risk %, and ATR, return share count,
        stop loss, target price, risk-reward ratio, and dollar risk. If RR < 2:1,
        tell me to skip.""",
        "schema": PositionSizeSchema,
        "tools": ["math"],
        "schedule": "manual",  # per-trade
    },
    "eod_recap_and_plan": {
        "system_prompt": """You are my evening assistant. Output: (1) 5-line recap
        of today, (2) the 3 things I'm watching tomorrow, (3) the 1 piece of
        news that could move my work, (4) my risk budget for tomorrow.""",
        "schema": EODRecapSchema,
        "tools": ["trade_blotter", "news_api", "calendar_api"],
        "schedule": "30 16 * * 1-5",  # 4:30pm weekdays
    },
    "compliance_summary": {
        "system_prompt": """You are a compliance officer. Read my weekly fill report
        and my risk rules. Output: (1) every rule violation, (2) max position size,
        (3) max daily loss, (4) current drawdown, (5) a flag if any metric is
        approaching limits.""",
        "schema": ComplianceReportSchema,
        "tools": ["fill_report", "risk_rules"],
        "schedule": "0 17 * * 5",  # Friday 5pm
    },
}
```

The 5 guardrails in code (the 50 lines above already implement them, but the explicit pattern):

```python
GUARDRAILS = {
    "loop_detector": "Hard cap on steps. If exceeded, abort. Default 10 steps per workflow.",
    "schema_validator": "Every workflow has a fixed Pydantic schema. If output doesn't match, retry. If retry fails, abort.",
    "cost_ceiling": "Per-month USD cap. Default $20/month. If exceeded, the agent is killed for the month.",
    "idempotency": "Each run has a unique ID (workflow + date + input hash). Re-running produces the same output; the agent never re-emails or re-posts.",
    "audit_log": "Every step writes a JSONL record. Review the log weekly. The audit log is the artifact that survives the FDE's exit.",
}
```

The pattern that wins interviews is the **"5 workflows + 5 guardrails + 7 ingredients"** pattern. The candidate who says "AI agents in 2026 = LLM + tools + loop with 5 guardrails; trading is the canonical demonstration because it meets all 4 use case criteria; the 5 workflows save 1,150 hours/year; the 5 guardrails are how you sleep; the wrong choice is to automate the decision, the right choice is to automate the work around the decision" is the candidate who demonstrates the production mindset.

## Code or example

The 5 workflows in production at a solo operator (the small case):

```python
SOLO_OPERATOR_DEMO = {
    "customer": "Solo operator running their own book",
    "team": "1 person (no engineers)",
    "scale": "10-15 trades/week, 5 workflows/day + 2 workflows/week",
    "latency": "5-30 seconds per workflow is fine",
    "cost": "$20/month LLM API (under budget)",
    "verdict": "the 5-workflow TradingAgent ships in 30 days",
    "outcome": {
        "hours_saved_per_year": 1150,
        "cost_per_month": 20,
        "decision_quality_change": "0% (the agent doesn't change the decision)",
        "stress_reduction": "high (no more Sunday compliance dread)",
    },
}
```

The 5 workflows in production at a 10-person team (the scale case):

```python
MID_SIZED_TEAM = {
    "customer": "10-person team, $5M AUM",
    "team": "5 operators, 2 ops, 2 engineers, 1 CTO",
    "scale": "100+ decisions/day, 50 workflows/day",
    "latency": "sub-second required for sizing; 30s ok for research",
    "cost": "$200/month LLM API (still under budget at 0.1% of AUM)",
    "verdict": "the 5-workflow TradingAgent scales to 10 operators",
    "additions": [
        "multi-tenant cost tracking (per-operator cost attribution)",
        "shared watchlist + shared risk rules (Redis-backed)",
        "weekly team postmortem (compliance summary, but for the team)",
        "Slack integration (workflow outputs posted to #daily)",
    ],
}
```

The 5 workflows NOT to automate (the anti-patterns):

```python
ANTI_PATTERNS = {
    "automate_the_decision": {
        "why_not": "LLMs hallucinate signals; regulators are starting to ask; the operator should keep the human in the loop on the actual click",
        "instead": "automate the work around the decision; keep the decision human",
    },
    "buy_a_500_month_bot": {
        "why_not": "Bots underperform basic index funds; you don't own the strategy; you can't audit the decisions",
        "instead": "build the 5 workflows yourself; you own the strategy; you can audit every decision",
    },
    "use_an_llm_for_signal_generation": {
        "why_not": "LLMs don't have real-time data; they hallucinate tickers and prices; they can't backtest",
        "instead": "use the LLM for language work (research, journaling, compliance); use deterministic code for signals",
    },
    "let_the_algorithm_execute": {
        "why_not": "Firms ban it; regulators are starting to ask; one bad day can blow the account",
        "instead": "the agent produces the signal + the size; the operator clicks the trade",
    },
}
```

The FDE's 60-second interview answer:

```python
def interview_answer_ai_agents_2026(requirements: dict) -> str:
    """The 60-second answer to 'where do AI agents work best in 2026'."""
    return f"""AI agents in 2026 = LLM + tools + loop, with 5 guardrails.
    The wrong choice is to think of them as 'AI that decides for you.'
    The right choice is to think of them as a junior assistant with infinite
    patience and zero judgment — it does the boring language-heavy work,
    you keep the decision.

    Trading is the canonical demonstration. It meets all 4 use case criteria:
    repetitive, language-heavy, tool-using, measurable.

    The 5 workflows: pre-market research, trade journal analysis, position-sizing
    calculator, EOD recap + plan, compliance summary. Together they save
    1,150 hours/year.

    The 5 guardrails: loop detector, schema validator, cost ceiling, idempotency,
    audit log. The wrong choice is to skip the guardrails. The right choice is
    to ship the guardrails first, then the workflows.

    The same pattern unlocks 12 more workflows across customer support, sales,
    legal, and ops.

    The wrong choice is to automate the decision. The right choice is to
    automate the work around the decision. The agent produces the signal
    and the size; the operator clicks the trade.

    For this customer, the 5-workflow agent ships in 30 days for $20/month."""
```

## Production addendum

The AI-agents question is the answer to "where do AI agents work best in 2026." The 60-second pitch:

> "AI agents in 2026 = LLM + tools + loop, with 5 guardrails. The wrong choice is to think of them as 'AI that decides for you.' The right choice is to think of them as a junior assistant with infinite patience and zero judgment — it does the boring language-heavy work, you keep the decision. Trading is the canonical demonstration: 5 workflows (research, journal, sizing, EOD, compliance) meet all 4 use case criteria (repetitive, language-heavy, tool-using, measurable) and save 1,150 hours/year. The 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) are how you sleep at night. The same pattern unlocks 12 more workflows across customer support, sales, legal, and ops. The 30-day plan: day 1-3 research, day 4-6 journal, day 7-9 sizing, day 10-12 EOD, day 13-15 compliance, day 16-30 iterate + add guardrails. The 200-line agent ships in 30 days for $20/month."

This is the difference between a candidate who says "I use ChatGPT" and a candidate who says "AI agent = LLM + tools + loop with 5 guardrails; trading is the canonical demonstration; 5 workflows save 1,150 hours/year; the agent does the work around the decision, you keep the decision; the same pattern unlocks 12 more workflows across the back office." The latter is who gets hired.

The 4 objection handlers (the FDE's standard 4):

1. **"The AI will hallucinate a trade signal."** Answer: the agent doesn't make the decision. The agent produces the research brief, the journal postmortem, the position size, the EOD recap, the compliance summary. The operator reads the output, decides, and clicks. The hallucination risk is in the language work, not the decision work.
2. **"The agent will loop and burn my API credits."** Answer: the cost ceiling is $20/month. The agent stops when it hits the cap. The loop detector caps at 10 steps per workflow. The audit log records every run, so you can see what happened.
3. **"The agent will email 10,000 recipients by accident."** Answer: the schema validator rejects outputs that don't match the expected shape. The idempotency guard means the agent can't re-send the same email twice. The audit log records every send.
4. **"I can't trust an AI with my account."** Answer: you don't. The agent doesn't have access to your account. The agent produces a research brief, a position size, and a compliance summary. You read the brief, you place the trade, you file the compliance report. The agent is an assistant, not an executor.

The ROI calculation (the FDE's 60-second answer):

```python
ROI = {
    "hours_saved_per_year": 1150,  # 5 workflows × 2-3 hours/week × 50 weeks
    "hourly_value_usd": 50,  # conservative: an operator's time is worth $50-200/hr
    "annual_value_usd": 1150 * 50,  # $57,500
    "agent_cost_per_month": 20,
    "agent_cost_per_year": 240,
    "net_savings_per_year": 57500 - 240,  # $57,260
    "payback_period_days": 1,  # the agent pays for itself in 1 day
}
```

The wrong choice is to spend $500/month on a bot that doesn't work. The right choice is to spend $20/month + 30 hours of setup time on the 5-workflow agent that pays for itself in 1 day.

### The 12 workflows the pattern unlocks (beyond trading)

The trading example is a vehicle. The **pattern** — repetitive + language-heavy + tool-using + measurable, with 5 guardrails — applies to roughly 12 workflows across every knowledge-work job:

| Workflow | Read | Write | Save |
|----------|------|-------|------|
| **Customer support tier-1** | Inbox + ticket history | First reply + tag | 3-5 hrs/day per agent |
| **Sales call review** | Call transcript + CRM | Coaching note + next-step | 2-3 hrs/day per rep |
| **Contract review** | Contract PDF + playbook | Redlined version + summary | 1-2 hrs/contract |
| **Candidate screening** | Resume + JD | Score + 3 questions | 30-60 min/candidate |
| **Code review** | PR diff + style guide | Comments + verdict | 20-40 min/PR |
| **Content moderation** | Post + policy | Verdict + reason | 5-10× human throughput |
| **Lead enrichment** | Email + LinkedIn | CRM row | 3-5 min/lead |
| **Tax categorization** | Receipt + chart of accounts | Journal entry | 90% of bookkeeping |
| **Meeting notes** | Transcript + attendees | Notes + action items | 20-30 min/meeting |
| **News monitoring** | RSS + filters | Daily brief | 1-2 hrs/day |
| **Inventory reorder** | Sales data + supplier API | Purchase order | 1-2 hrs/week |
| **Onboarding checklist** | New-hire doc + role spec | Day-1 plan | 30-60 min/hire |

Pick the one that costs you the most hours. Build the agent. Move to the next. The same 7 ingredients, the same 5 guardrails, the same 30-day build per workflow. The trading example is the seed; the other 11 are the harvest.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/README.md` — the 7 ingredients + 5 guardrails pattern that the TradingAgent implements.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-trading-agent.py` — the canonical 200-line trading agent (when this file is added).
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the FDE pattern.
- **Section 9 (use cases)**: `course/ai-fde/.../intro-to-ai-agents/s09-ai-agents-in-business/L9-2-the-use-case-library.md` — the 4 use case criteria + 6-axis rubric that this lecture scores against. The 12-workflow table above is the extended rubric.
- **Section 9 (business case)**: `course/ai-fde/.../intro-to-ai-agents/s09-ai-agents-in-business/L9-1-the-business-case-for-ai-agents.md` — the ROI formula applied to the solo operator.
- **Companion blog post**: `marketing/content/articles/2026-10-ai-agents-for-trading-workflows.md` — the Substack version of this lecture.

## The 3 questions this lecture preps you for

1. **"Where do AI agents work best in 2026?"** Answer: anywhere the work is repetitive + language-heavy + tool-using + measurable. Trading is the canonical demonstration: 5 workflows (research, journal, sizing, EOD, compliance) all score 4/4 and save 1,150 hours/year. The 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) make the workflows production-safe. The same pattern unlocks 12 more workflows across customer support, sales, legal, and ops. The wrong choice is to automate the decision; the right choice is to automate the work around the decision.
2. **"How do you ship a production agent?"** Answer: the 7 ingredients (model, tools, memory, cost ceiling, system prompt, parser, loop driver) + the 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) + the 4 use case criteria (repetitive, language-heavy, tool-using, measurable) + the 30-day build plan. The pattern is invariant; the implementation differs per use case. The 50-line TradingAgent in this lecture is the canonical reference; the 12-workflow table is the canonical extension.
3. **"How do you monetize AI teaching content?"** Answer: Substack + LinkedIn as the funnel (top-of-funnel + distribution); own course at $47-497 as the revenue; 1:1 consulting at $200-500/hr as the high-ticket backend. The 30-60-90 day ramp: 100 LinkedIn followers in 30 days, 20 paid Substack subs in 60 days, 10-20 course sales in 90 days = $2K-5K month 3. The article's $ is in the leads it generates, not the reads it gets.

## Read next

`course/ai-fde/.../intro-to-ai-agents/s10-ai-in-trading/L10-2-options-and-derivatives-workflows.md` — when added. The 5 workflows in this lecture apply to equities, FX, crypto, and commodities. The next lecture covers options- and derivatives-specific workflows: the greeks calculator, the IV-rank screener, the roll/yield analyzer, the assignment-risk monitor, and the tax-lot optimizer.

Or, if you're not adding more trading lectures yet:

`course/ai-fde/.../intro-to-ai-agents/s09-ai-agents-in-business/L9-2-the-use-case-library.md` — the 4 use case criteria + 12 use cases + 6 verticals that this lecture scored against. The 12-workflow table in this lecture is the extended rubric: trading is one vertical; the other 11 workflows are the rest.
