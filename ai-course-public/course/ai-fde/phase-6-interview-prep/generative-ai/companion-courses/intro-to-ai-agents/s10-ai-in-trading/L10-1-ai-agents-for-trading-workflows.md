# L10.1: AI agents for trading workflows — the 5 workflows + 5 guardrails

> **FDE framing in one line:** trading is the canonical use case for AI agents in 2026: it is repetitive, language-heavy, tool-using, and measurable. The 5 workflows (research, journal, sizing, EOD, compliance) are automatable in 30 days; the 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) are how the solo trader sleeps at night. The wrong choice is to automate the trade decision; the right choice is to automate the work around the trade.

## In 60 seconds

> "5 workflows. Pre-market research (5am, news + filings + social → 1-page brief, 30s to read). Trade journal analysis (Sunday, broker CSV → postmortem, 5min to read). Position-sizing calculator (per trade, account × risk × ATR → share count + stop + target). EOD recap + plan (4:30pm, trades + news + calendar → 1-page plan). Compliance summary (Friday, fills + risk rules → 1-page audit). 5 guardrails: loop detector (cap at 10 steps), schema validator (fixed output shape), cost ceiling ($20/month), idempotency (no duplicate runs), audit log (write every decision). $20/month LLM API + Notion + 1 hour/day for 30 days = 1,150 hours/year back. The wrong choice is to buy a $500/month bot. The right choice is the 5 workflows + 5 guardrails + 30-day plan."

**The wrong choice is to read past this block.** The right choice is to recite the 5 workflows + 5 guardrails before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. **The 5 trading workflows** that meet all 4 use case criteria (repetitive, language-heavy, tool-using, measurable): pre-market research, trade journal analysis, position-sizing calculator, EOD recap + plan, compliance summary. Each saves 1-3 hours/week; the 5 together save 1,150 hours/year.
2. **The 5 guardrails** that make the workflows production-safe: loop detector, schema validator, cost ceiling, idempotency, audit log. These are the same 5 from Section 6.5, applied to the trading-agent context. Without them, the agent loops, hallucinates, or runs up a $2,000 API bill.
3. **The 30-day build plan** — day-by-day what to build, in what order, with what tools. Day 1-3: pre-market research. Day 4-6: journal. Day 7-9: sizing. Day 10-12: EOD. Day 13-15: compliance. Day 16-30: iterate, debug, add the 5 guardrails. By day 30, the 5 agents run for you every day.

## Concept

Trading is the canonical use case for AI agents in 2026. The 4 use case criteria from L9.2 — **repetitive, language-heavy, tool-using, measurable** — all four apply to almost every workflow in a trading day. The FDE's job is to identify which workflows meet all 4, build the agent, and ship it.

The 5 trading workflows that meet all 4 criteria:

| # | Workflow | Repetitive | Language | Tool-using | Measurable | Time saved |
|---|----------|------------|----------|------------|------------|------------|
| 1 | Pre-market research | Daily 5am | Yes (news) | News API + filings | Brief on time | 2-3 hours/day |
| 2 | Trade journal analysis | Weekly Sun | Yes (postmortem) | CSV read + LLM | Postmortem written | 2-3 hours/week |
| 3 | Position-sizing calculator | Per trade | Yes (output) | Math + LLM | Numbers correct | 1-2 min/trade |
| 4 | EOD recap + plan | Daily 4:30pm | Yes (recap + plan) | Blotter + news | Plan before 5pm | 1-2 hours/day |
| 5 | Compliance summary | Weekly Fri | Yes (audit) | Fill report + rules | Report sent | 2-3 hours/week |

Each workflow scores 4/4 on the use case rubric. Each saves a measurable amount of time. Each is automatable with off-the-shelf tools (LLM API + Notion + a spreadsheet + a cron job).

**The 5 workflows that DON'T meet the 4 criteria** (and should not be automated):

- **The actual trade decision** (criteria fail: not repetitive per se; not measurable — P&L is too noisy; not tool-using in the LLM sense)
- **Strategy development** (criteria fail: not repetitive; not language-heavy enough; not measurable in the short term)
- **Risk management on novel events** (criteria fail: not repetitive; human judgment required)
- **Relationship management with broker / prop firm** (criteria fail: not tool-using via API; high context)
- **The "I have a feeling" trade** (criteria fail: not measurable; the feeling is the point)

The wrong choice is to try to automate the trade decision itself. The right choice is to automate the work around the trade and keep the human in the loop on the actual click.

The 4 use case criteria applied to trading (the FDE's filter):

1. **Repetitive.** The workflow happens > 1×/day or 1×/week. Pre-market research is daily; journal is weekly; sizing is per-trade. Strategy development is not.
2. **Language-heavy.** The workflow is text or speech. Research is text; journal is text; compliance is text. Order execution is not.
3. **Tool-using.** The workflow calls an API or reads a file. Research calls a news API; journal reads a CSV; compliance reads a fill report. "Thinking about the market" is not.
4. **Measurable.** The output is verifiable. A research brief is on-time + covers the top 3 catalysts (verifiable). A trade decision is not (P&L is too noisy).

The 5 workflows above score 4/4. The 5 workflows that don't (including the trade decision) score 1-2/4. **The filter is the FDE's first line of defense against over-automation.**

## The pattern

The 5 workflows + 5 guardrails, as a single production pattern. The same 7 ingredients + 5 guardrails from Section 2, instantiated for the trading-agent context.

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
| Loop detector | Hard cap at 10 steps; if exceeded, abort and alert the trader |
| Schema validator | Output must match fixed JSON shape; if not, retry; if retry fails, abort |
| Cost ceiling | $20/month LLM API; if exceeded, kill the agent for the month |
| Idempotency | The same input produces the same output; the agent never re-emails the same brief |
| Audit log | Every run writes {timestamp, workflow, input, output, cost} to a JSONL file |

The 5 workflows as a single TradingAgent class (the FDE pattern, 50 lines):

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

The 5 workflow definitions (the 5 system prompts + 5 schemas, from the blog post):

```python
WORKFLOWS = {
    "pre_market_research": {
        "system_prompt": """You are a pre-market research analyst for a Singapore-based
        equity trader. Read these 50 news items and 20 SEC filings. Output a 1-page
        brief with: (1) top 3 catalysts for the watchlist, (2) top 3 risks, (3) top 3
        things to watch today. Rank by relevance. Keep under 500 words.""",
        "schema": PreMarketBriefSchema,  # Pydantic
        "tools": ["news_api", "filings_api"],
        "schedule": "0 5 * * 1-5",  # 5am weekdays
    },
    "trade_journal_analysis": {
        "system_prompt": """You are a trading psychologist and risk analyst. Read my
        trade journal CSV. Output: (1) 5 patterns I should be aware of, (2) the 3
        trades that hurt the most, (3) my best and worst setups, (4) one rule I
        should add. Be direct.""",
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
        "system_prompt": """You are my evening trading assistant. Output: (1) 5-line
        recap of today, (2) the 3 setups I'm watching tomorrow, (3) the 1 piece of
        news that could move my watchlist, (4) my risk budget for tomorrow.""",
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
    "loop_detector": "Hard cap on steps. If exceeded, abort. The default cap is 10 steps per workflow.",
    "schema_validator": "Every workflow has a fixed Pydantic schema. If the LLM output doesn't match, retry. If retry fails, abort.",
    "cost_ceiling": "Per-month USD cap. Default $20/month. If exceeded, the agent is killed for the month.",
    "idempotency": "Each run has a unique ID (workflow + date + input hash). Re-running the same input produces the same output; the agent never re-emails or re-posts.",
    "audit_log": "Every step writes a JSONL record. Review the log weekly. The audit log is the artifact that survives the FDE's exit.",
}
```

The pattern that wins interviews is the "5 workflows + 5 guardrails + 7 ingredients" pattern. The candidate who says "trading is the canonical use case for AI agents because it meets all 4 use case criteria; the 5 workflows save 1,150 hours/year; the 5 guardrails are how the trader sleeps at night; the wrong choice is to automate the trade decision, the right choice is to automate the work around the trade" is the candidate who demonstrates the production mindset.

## Code or example

The 5 workflows in production at a Singapore-based prop firm (the case study):

```python
PACIFIC_FREIGHT_TRADER_DEMO = {
    "customer": "Solo prop trader, Singapore, $50K account, FTMO challenge",
    "team": "1 trader (no engineers), 1 ops person part-time",
    "scale": "10-15 trades/week, 5 workflows/day + 2 workflows/week",
    "latency": "5-30 seconds per workflow is fine",
    "cost": "$20/month LLM API (under budget)",
    "verdict": "the 5-workflow TradingAgent ships in 30 days",
    "outcome": {
        "hours_saved_per_year": 1150,
        "cost_per_month": 20,
        "win_rate_change": "0% (the agent doesn't change the win rate)",
        "stress_reduction": "high (no more Sunday compliance dread)",
    },
}
```

The 5 workflows in production at a 10-person trading shop (the scale case):

```python
MID_SIZED_TRADING_SHOP = {
    "customer": "10-person trading shop, Singapore, $5M AUM",
    "team": "5 traders, 2 ops, 2 engineers, 1 CTO",
    "scale": "100+ trades/day, 50 workflows/day",
    "latency": "sub-second required for sizing; 30s ok for research",
    "cost": "$200/month LLM API (still under budget at 0.1% of AUM)",
    "verdict": "the 5-workflow TradingAgent scales to 10 traders",
    "additions": [
        "multi-tenant cost tracking (per-trader cost attribution)",
        "shared watchlist + shared risk rules (Redis-backed)",
        "weekly team postmortem (compliance summary, but for the team)",
        "Slack integration (workflow outputs posted to #trading-daily)",
    ],
}
```

The 5 workflows NOT to automate (the anti-patterns):

```python
ANTI_PATTERNS = {
    "automate_the_trade_decision": {
        "why_not": "LLMs hallucinate signals; regulators are starting to ask; the trader should keep the human in the loop on the actual click",
        "instead": "automate the work around the trade; keep the trade decision human",
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
        "why_not": "Prop firms ban it; regulators are starting to ask; one bad day can blow the account",
        "instead": "the agent produces the signal + the size; the trader clicks the trade",
    },
}
```

The FDE's 60-second interview answer:

```python
def interview_answer_trading_agents(requirements: dict) -> str:
    """The 60-second answer to 'how do you use AI for trading'."""
    return f"""Trading is the canonical use case for AI agents in 2026.
    It meets all 4 use case criteria: repetitive, language-heavy, tool-using,
    measurable.

    The 5 workflows: pre-market research, trade journal analysis, position-sizing
    calculator, EOD recap + plan, compliance summary. Together they save
    1,150 hours/year.

    The 5 guardrails: loop detector, schema validator, cost ceiling, idempotency,
    audit log. The wrong choice is to skip the guardrails. The right choice is
    to ship the guardrails first, then the workflows.

    The wrong choice is to automate the trade decision. The right choice is to
    automate the work around the trade. The agent produces the signal and the
    size; the trader clicks the trade.

    For this customer, the 5-workflow TradingAgent ships in 30 days for $20/month."""
```

## Production addendum

The trading-agent question is the answer to "where do AI agents work best in 2026." The 60-second pitch:

> "Trading is the canonical use case. The 5 workflows (research, journal, sizing, EOD, compliance) meet all 4 use case criteria: repetitive, language-heavy, tool-using, measurable. The 5 workflows save 1,150 hours/year. The 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) are how the trader sleeps at night. The wrong choice is to automate the trade decision; the right choice is to automate the work around the trade. The 30-day plan: day 1-3 research, day 4-6 journal, day 7-9 sizing, day 10-12 EOD, day 13-15 compliance, day 16-30 iterate + add guardrails. The 200-line TradingAgent ships in 30 days for $20/month."

This is the difference between a candidate who says "I use ChatGPT for trading" and a candidate who says "5 workflows, 5 guardrails, 7 ingredients, 1,150 hours/year saved, $20/month cost, the agent produces the signal, the trader clicks the trade." The latter is who gets hired.

The 4 objection handlers (the FDE's standard 4):

1. **"The AI will hallucinate a trade signal."** Answer: the agent doesn't make the trade decision. The agent produces the research brief, the journal postmortem, the position size, the EOD recap, the compliance summary. The trader reads the output, decides, and clicks. The hallucination risk is in the language work, not the trade work.
2. **"The agent will loop and burn my API credits."** Answer: the cost ceiling is $20/month. The agent stops when it hits the cap. The loop detector caps at 10 steps per workflow. The audit log records every run, so you can see what happened.
3. **"The agent will email 10,000 recipients by accident."** Answer: the schema validator rejects outputs that don't match the expected shape. The idempotency guard means the agent can't re-send the same email twice. The audit log records every send.
4. **"I can't trust an AI with my trading account."** Answer: you don't. The agent doesn't have access to your broker account. The agent produces a research brief, a position size, and a compliance summary. You read the brief, you place the trade, you file the compliance report. The agent is an assistant, not an executor.

The ROI calculation for the solo trader (the FDE's 60-second answer):

```python
TRADER_ROI = {
    "hours_saved_per_year": 1150,  # 5 workflows × 2-3 hours/week × 50 weeks
    "hourly_value_usd": 50,  # conservative: a prop trader's time is worth $50-200/hr
    "annual_value_usd": 1150 * 50,  # $57,500
    "agent_cost_per_month": 20,
    "agent_cost_per_year": 240,
    "net_savings_per_year": 57500 - 240,  # $57,260
    "payback_period_days": 1,  # the agent pays for itself in 1 day
}
```

The wrong choice is to spend $500/month on a bot that doesn't work. The right choice is to spend $20/month + 30 hours of setup time on the 5-workflow TradingAgent that pays for itself in 1 day.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/README.md` — the 7 ingredients + 5 guardrails pattern that the TradingAgent implements.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-trading-agent.py` — the canonical 200-line trading agent (when this file is added).
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the FDE pattern.
- **Section 9 (use cases)**: `course/ai-fde/.../intro-to-ai-agents/s09-ai-agents-in-business/L9-2-the-use-case-library.md` — the 4 use case criteria + 6-axis rubric that this lecture scores against.
- **Section 9 (business case)**: `course/ai-fde/.../intro-to-ai-agents/s09-ai-agents-in-business/L9-1-the-business-case-for-ai-agents.md` — the ROI formula applied to the solo trader.
- **Companion blog post**: `marketing/content/articles/2026-10-ai-agents-for-trading-workflows.md` — the Substack version of this lecture.
- **Singapore prop-firm data**: [MarketMates — Top 6 Prop Trading Firms in Singapore 2026](https://marketmates.com/learn/best-prop-trading-firms-singapore/) — the 6 firms (FTMO, The5ers, FundedNext, FXIFY, Blueberry, MarketMates) and the standard 10% profit target / 3-5% daily max loss challenge.

## The 3 questions this lecture preps you for

1. **"Where do AI agents work best?"** Answer: trading is the canonical use case in 2026. It meets all 4 use case criteria: repetitive, language-heavy, tool-using, measurable. The 5 workflows (research, journal, sizing, EOD, compliance) save 1,150 hours/year. The 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) make the workflows production-safe. The wrong choice is to automate the trade decision; the right choice is to automate the work around the trade.
2. **"How do you ship a production agent?"** Answer: the 7 ingredients (model, tools, memory, cost ceiling, system prompt, parser, loop driver) + the 5 guardrails (loop detector, schema validator, cost ceiling, idempotency, audit log) + the 4 use case criteria (repetitive, language-heavy, tool-using, measurable) + the 30-day build plan. The pattern is invariant; the implementation differs per use case.
3. **"How do you monetize AI teaching content?"** Answer: Substack + LinkedIn as the funnel (top-of-funnel + distribution); own course at $47-497 as the revenue; 1:1 consulting at $200-500/hr as the high-ticket backend. The 30-60-90 day ramp: 100 LinkedIn followers in 30 days, 20 paid Substack subs in 60 days, 10-20 course sales in 90 days = $2K-5K month 3. The article's $ is in the leads it generates, not the reads it gets.

## Read next

`course/ai-fde/.../intro-to-ai-agents/s10-ai-in-trading/L10-2-options-and-derivatives-workflows.md` — when added. The 5 workflows in this lecture apply to equities, FX, crypto, and commodities. The next lecture covers options- and derivatives-specific workflows: the greeks calculator, the IV-rank screener, the roll/yield analyzer, the assignment-risk monitor, and the tax-lot optimizer.

Or, if you're not adding more trading lectures yet:

`course/ai-fde/.../intro-to-ai-agents/s09-ai-agents-in-business/L9-2-the-use-case-library.md` — the 4 use case criteria + 12 use cases + 6 verticals that this lecture scored trading against. Trading is a new vertical the rubric can be extended to cover.
