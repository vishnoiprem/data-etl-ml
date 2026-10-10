# The AI Trading Agent That Runs While You Sleep: 5 Workflows a Solo Trader Can Automate in 30 Days

*A solo-trader playbook for the prop-firm era — 5 specific AI workflows that give you back 10+ hours a week, with the exact tools, prompts, and guardrails.*

---

A friend of mine — a Singapore-based prop trader I met at a kopi shop in Tanjong Pagar — used to work 60 hours a week. Pre-market research at 5am. Journal reviews at midnight. Position sizing recalculated by hand. Compliance summaries he wrote on Sundays, dreading them.

Last month, he told me he works 25 hours a week. Same prop-firm account. Same strategy. Same P&L.

The difference: he stopped doing the **5 boring workflows** himself. He built AI agents for each. The agents run at 5am, 9:30am, 4:30pm, and Sunday morning. He reviews their output, clicks the trades, and goes back to sleep.

This article is those 5 workflows. If you're a prop trader, a part-time retail trader, or a small-business owner who also trades your own book — these will save you 10+ hours a week. They will not make you a better trader. They will give you back the time to *be* a better trader.

Let's get into it.

---

## The wrong way to use AI in trading

Most "AI for trading" content is wrong. It tells you to:

- Buy a $500/month bot that promises 80% win rates
- Use an LLM to generate trade signals
- Let an algorithm execute for you

All three are traps. The bots underperform a basic index fund. LLMs hallucinate signals. Algorithm execution is what prop firms ban you for (and what regulators are starting to ask about).

**The right way to use AI in trading:** automate the **boring, repetitive, language-heavy** work around the trade — research, journaling, sizing, EOD recaps, compliance — and keep the human in the loop on the **actual click**. The agents don't make you money. They give you the time and the discipline to make money yourself.

---

## The 5 workflows (the canonical list)

Each workflow meets the same 4 criteria: **repetitive** (> 1×/day or 1×/week), **language-heavy** (text or speech), **tool-using** (calls an API or reads a file), **measurable** (verifiable output). If a workflow doesn't meet all 4, don't automate it.

### Workflow 1: Pre-market research (saves 2-3 hours/day)

Every morning at 5am, an AI agent scrapes 3 sources for you: the news API (newsapi.org or Google News), the SEC/equivalent filings feed for your watchlist, and Twitter/X for the 20 handles you follow. It ranks each item by relevance to your watchlist (keyword match + LLM scoring), deduplicates, and writes a 1-page brief: top 3 catalysts, top 3 risks, top 3 things to watch.

**Tools:** ChatGPT (or Claude, or Gemini) + a $5/month news API + a $15/month LLM API key.

**The prompt (give this to your agent):**

> *You are a pre-market research analyst for a Singapore-based equity trader. Read these 50 news items and 20 SEC filings. Output a 1-page brief with: (1) top 3 catalysts for the watchlist, (2) top 3 risks, (3) top 3 things to watch today. Rank by relevance to my watchlist: [paste your watchlist]. Keep the brief under 500 words. If a catalyst affects multiple watchlist names, list it once.*

**Time saved:** 2-3 hours/day → 30 seconds to skim the brief. **Annual value:** ~600 hours.

### Workflow 2: Trade journal analysis (saves 2-3 hours/week)

Every Sunday at 9am, an AI agent reads your broker CSV export (Interactive Brokers, Tiger, Saxo, Moomoo — all export CSV), parses every trade, and writes a weekly postmortem. It flags patterns: revenge trades (a loss followed by a same-day trade 2x your average size), over-sizing (any trade > 3% of account), time-of-day clusters (you lose money between 2-3pm, you didn't know), and P&L attribution by setup.

**Tools:** ChatGPT + your broker's CSV export + a Google Sheet.

**The prompt:**

> *You are a trading psychologist and risk analyst. Read my trade journal CSV (columns: date, time, ticker, side, qty, price, pnl, setup). Output: (1) 5 patterns I should be aware of, (2) the 3 trades that hurt the most and what setup they were, (3) my best-performing setup and my worst, (4) one rule I should add to my trading plan this week. Be direct. Don't soften the bad news.*

**Time saved:** 2-3 hours/week → 5 minutes to read the postmortem. **Annual value:** ~120 hours.

### Workflow 3: Position-sizing calculator (saves 1-2 minutes/trade, ~30 seconds)

Before every trade, instead of doing the math in your head (or worse, eyeballing it), an AI agent takes your account size, your risk % (default 1%), and the ATR (Average True Range) of the stock, and returns: share count, stop price (ATR × 1.5 below entry), target price (ATR × 3 above entry), and the risk-reward ratio. The wrong choice is to skip the math. The right choice is to have the agent do the math in 30 seconds so you always size correctly.

**Tools:** ChatGPT + a Google Sheet with the ATR formula.

**The prompt:**

> *I have an account size of $[X]. My risk per trade is [Y]%. The stock is $[Z] and has an ATR of $[A]. Entry is $[E]. Output: (1) number of shares to buy, (2) stop loss price, (3) target price at 3× ATR, (4) risk-reward ratio, (5) the dollar amount I risk on this trade. If the risk-reward is below 2:1, tell me to skip the trade.*

**Time saved:** 1-2 minutes/trade × 50 trades/month = 50-100 minutes/month. **Annual value:** ~15 hours + the trades you don't blow up on because you sized correctly.

### Workflow 4: EOD recap + tomorrow's plan (saves 1-2 hours/day)

At 4:30pm every weekday, an AI agent reads: today's trades, today's news, tomorrow's economic calendar (CPI, FOMC, NFP — whatever's scheduled), and your watchlist. It writes a 1-page EOD recap (what you did, what worked, what didn't) and a 1-page plan for tomorrow (top 3 setups, key levels, the news that could move the market).

**Tools:** ChatGPT + your trade blotter + a $5/month economic calendar API.

**The prompt:**

> *You are my evening trading assistant. Read my trades today, the news that moved the market, and tomorrow's economic calendar. Output: (1) a 5-line recap of today (what I did right, what I did wrong), (2) the 3 setups I'm watching tomorrow, (3) the 1 piece of news that could move my watchlist, (4) my risk budget for tomorrow in dollars. Be honest. If I traded badly, say so.*

**Time saved:** 1-2 hours/day → 10 minutes to read. **Annual value:** ~300 hours.

### Workflow 5: Compliance / post-trade ops (saves 2-3 hours/week)

Every Friday at 5pm, an AI agent reads your weekly fills, checks them against your risk rules (max position size, max daily loss, max drawdown, restricted tickers), and emails you a compliance summary. The wrong choice is to do this manually on Sunday and dread it. The right choice is to have the agent do it Friday afternoon so you can review and file before the weekend.

**Tools:** ChatGPT + your broker fill report + a $5/month email automation tool (Mailgun, Resend).

**The prompt:**

> *You are a compliance officer. Read my weekly fill report and my risk rules: [paste rules]. Output: (1) every trade that violated a rule, with the rule and the date, (2) the maximum position size I held, (3) the maximum daily loss, (4) my current drawdown vs peak, (5) a flag if any metric is approaching my limits. If everything is clean, say so in one line.*

**Time saved:** 2-3 hours/week → 10 minutes to review. **Annual value:** ~120 hours.

**Total time saved across all 5 workflows: ~1,150 hours/year.** That is roughly half of a full-time job's worth of time back, every year.

---

## The 3 things you actually need

You don't need a $500/month bot. You need 3 things:

1. **A paid LLM API key** ($20/month for ChatGPT Plus or $5-30/month for direct API access). The API is the engine.
2. **A spreadsheet or Notion to store the data** (free). Your broker CSV exports, your watchlist, your risk rules. The data is the fuel.
3. **1 hour a day for 30 days** to set this up. Day 1: workflow 1. Day 2: workflow 2. By day 30, all 5 are running.

The wrong choice is to buy a $500/month trading bot. The right choice is to spend 30 hours setting up the 5 agents that work for you for the next 5 years.

---

## The 5 guardrails (the part most "AI trading" articles skip)

Your agents are dumb. They'll loop. They'll hallucinate. They'll try to email 10,000 recipients if you let them. The 5 guardrails are how you sleep at night:

1. **Loop detector.** Set a hard cap on agent steps. If the agent has tried 10 things and still hasn't finished, kill it. The wrong choice is to let an agent run for 3 hours burning API credits.
2. **Schema validator.** The agent's output must match a fixed structure (date, ticker, action, size, price). If the structure is wrong, the agent retries. If it can't fix it, the agent aborts. The wrong choice is to trust free-form output.
3. **Cost ceiling.** Cap your LLM spend at $20/month. The agent stops when it hits the cap. The wrong choice is to leave the wallet open and discover a $2,000 bill.
4. **Idempotency.** The same input produces the same output. Don't let the agent email the compliance summary twice because you clicked "Run" twice. The wrong choice is to wake up to 5 duplicate emails at 3am.
5. **Audit log.** Every agent run writes a record: what it read, what it decided, what it sent. Review the log weekly. The wrong choice is to trust the agent without looking.

The 5 guardrails are the difference between a $20/month habit and a $2,000/month disaster.

---

## Where the money actually comes from (a real answer)

You asked. Here's the honest answer: **Substack and Medium pay pennies. LinkedIn and your own course pay the bills.**

| Platform | How you make money | Milestone to first $100 | Best for |
|----------|--------------------|--------------------------|----------|
| **Substack** | Paid subscriptions ($5-10/month, you keep 90%) | 20 paid subs = $100/mo (3-6 months) | Recurring revenue + lead-gen |
| **Medium** | Per-read payout from a fixed monthly pool | Variable, $5-30 per 1K reads (1-3 months) | One-off viral posts; SEO long-tail |
| **LinkedIn** | No ads — you build authority, get DMs, sell your own course | 1 lead/week in 1-4 weeks | B2B / consulting / high-trust audience |
| **Your own course** (Gumroad, Teachable, your own site) | Direct sales at $47-497/course, 95% margin | 1-3 sales/week = $100-500 (2-8 weeks) | Highest LTV; you own the list |
| **YouTube** | AdSense ($2-8 per 1K views) + sponsorships | 1K-10K subs for $100/mo (6-12 months) | Long-tail discovery; SEO |

**The funnel that actually works for an AI teaching business in Asia:**

- **Days 1-30:** Post 3-5×/week on LinkedIn. Write 1 Substack article. Get to 100 LinkedIn followers. First 5 DMs from readers.
- **Days 31-60:** Get to 500 LinkedIn followers. 5 Substack articles. 20 paid Substack subs. First $100.
- **Days 61-90:** Launch the $97 course. 10-20 sales from LinkedIn + Substack = $1K-2K. First consulting client at $200-500/hr = $1K-3K. **Total: $2K-5K by month 3.**

Substack is the top of the funnel. LinkedIn is the distribution. Your own course is the revenue. 1:1 consulting at $200-500/hr is the high-ticket backend. **The article's $ is in the leads it generates, not the reads it gets.**

---

## Your 30-day plan (the 5 workflows, day by day)

| Day | Workflow | Time | What you build |
|-----|----------|------|----------------|
| 1-3 | Pre-market research | 3 hours | News API + ChatGPT prompt + cron job (5am daily) |
| 4-6 | Trade journal analysis | 3 hours | Broker CSV export + ChatGPT prompt + Sunday cron |
| 7-9 | Position-sizing calculator | 2 hours | Google Sheet + ATR formula + ChatGPT prompt |
| 10-12 | EOD recap + tomorrow's plan | 3 hours | Trade blotter + news API + ChatGPT prompt + 4:30pm cron |
| 13-15 | Compliance summary | 3 hours | Fill report + risk rules + ChatGPT prompt + Friday cron |
| 16-30 | Iterate, debug, refine prompts | 10 hours | Add the 5 guardrails; check the audit logs; tune the prompts |

After day 30, you have 5 agents that run for you every day. The agents don't sleep. They don't take weekends off. They don't argue with you about whether to size up.

You do.

---

## Want the full system?

I built a free 5-day email course that walks you through setting up all 5 workflows, with the exact prompts, the exact guardrails, and the exact 30-day plan. Reply "AGENTS" to this email or click the link below.

→ [Free 5-day email course: 5 AI workflows for the solo trader](#)

And if you want the full trading-agent system — the 200-line Python script, the eval set, the model card, the runbook — that's in the **AI for Prop Traders** course (launching month 3, $97).

The agents don't make you money. They give you the time and the discipline to make money yourself.

That's the whole game.

— Vishnoi

---

**Sources for the numbers in this article:**

- [Write • Build • Scale — Medium vs Substack (real subscriber math, 2025)](https://writebuildscale.substack.com/p/medium-vs-substack-comparison)
- [Better Marketing — Medium vs Substack vs LinkedIn](https://bettermarketing.pub/best-platform-for-writers-to-make-more-than-1000-per-month-medium-vs-substack-vs-linkedin-a16c6b91c56b)
- [Mark Schaefer — Is it time to monetize your audience through Substack?](https://www.linkedin.com/pulse/time-monetize-your-audience-through-substack-mark-schaefer-jmhqe)
- [MarketMates — Top 6 Prop Trading Firms in Singapore 2026](https://marketmates.com/learn/best-prop-trading-firms-singapore/)

*This article is the Substack version of L10.1 in the [FDE course](https://github.com/your-repo/course/ai-fde/phase-6-interview-prep/generative-ai/companion-courses/intro-to-ai-agents/s10-ai-in-trading/). The course version has the 200-line Python TradingAgent class, the 7 ingredients, the 5 guardrails, and the 8-section template.*
