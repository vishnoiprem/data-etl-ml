# The 5 AI Agents That Run While You Sleep (And Why 2026 Is the Year the Boring Work Disappears)

*A field guide to the new shape of work: AI agents that take the language-heavy, tool-using, repetitive tasks off your plate — using trading workflows as the canonical example.*

---

A friend of mine — solo operator, runs his own book — used to grind 60 hours a week. Pre-market research at 5am. Journal reviews at midnight. Position sizing recalculated by hand. Weekly compliance summaries he dreaded.

Last month, he told me he works 25 hours a week. Same account. Same strategy. Same P&L.

The difference: he stopped doing **5 boring workflows** himself. He built an **AI agent** for each. The agents run at 5am, 9:30am, 4:30pm, and Sunday morning. He reviews their output, makes the actual call, and goes back to sleep.

This article is about those 5 agents. But the real story isn't trading. The real story is **what AI agents are good at in 2026** — and the answer is: **boring, repetitive, language-heavy work that nobody wants to do.** Trading just happens to be the cleanest example I know. The same 5 patterns apply to legal review, customer support, sales ops, accounting, content moderation, and roughly 30 other back-office workflows.

Let's get into it.

---

## What an AI agent actually is (and isn't)

Strip away the hype. An AI agent in 2026 is a small piece of software with three things bolted on: **a language model** (LLM) that reads and writes text, **tools** it can call (APIs, files, spreadsheets, your inbox, your broker), and **a loop** that lets it try → check → retry until the job is done.

That's it. No magic. No sentience. No AGI. An agent is **a junior assistant with infinite patience and zero judgment** — it will scrape 50 news items at 5am, write you a 1-page brief, and never complain. It will also loop forever, hallucinate a trade signal, and try to email 10,000 people if you let it. The whole art of building agents is giving them **guardrails** so they help instead of hurt.

**The wrong way to think about agents in 2026:** "the AI will trade for me" or "the AI will replace my analyst." Both are wrong. Models hallucinate signals. Regulators flag autonomous execution. Your judgment is the moat.

**The right way to think about agents:** they take the **language-heavy, tool-using, repetitive** work **off your plate** and leave the **actual decision** to you. The agent writes the brief. You read the brief and click the trade. The agent drafts the compliance summary. You sign it. The agent logs the customer call. You handle the escalation.

**Before you automate anything, score it against 4 criteria.** If a workflow doesn't hit all 4, **don't automate it** — the agent will be worse than you: (1) **repetitive** (>1×/day or 1×/week), (2) **language-heavy** (text or speech), (3) **tool-using** (reads a file, calls an API), (4) **measurable** (verifiable output). "Decide whether to hire this person" fails. "Negotiate the deal" fails. "The actual trade decision" fails. Every workflow in this article passes.

---

## The 5 agents (the canonical pattern, demonstrated on trading)

Each agent follows the same shape: **a cron job wakes the agent → reads inputs → calls an LLM with a fixed prompt → validates the output against a schema → writes the result to a file or sends an email → goes back to sleep.** Total setup: 1-3 hours per agent. Total runtime cost: $2-5/month per agent on a paid LLM API.

### Agent 1: Pre-market research

**What it does:** every morning at 5am, the agent scrapes 3 sources (news API, your regulator's filings feed, and the 20 social handles you follow), ranks each item by relevance to your watchlist, deduplicates, and writes a 1-page brief: top 3 catalysts, top 3 risks, top 3 things to watch.

**The prompt (lift this verbatim):**

> *You are a research analyst. Read these 50 items and rank by relevance to my watchlist: [paste your watchlist]. Output a 1-page brief with: (1) top 3 catalysts, (2) top 3 risks, (3) top 3 things to watch today. Under 500 words. If a catalyst affects multiple watchlist names, list it once.*

**Time saved:** 2-3 hours/day → 30 seconds to skim. **Annual value:** ~600 hours.

### Agent 2: Trade journal analysis

**What it does:** every Sunday at 9am, the agent reads your broker's CSV export, parses every trade, and writes a weekly postmortem. It flags patterns: revenge trades, over-sizing, time-of-day clusters, P&L by setup.

**The prompt:**

> *You are a performance analyst. Read my trade journal CSV (columns: date, time, ticker, side, qty, price, pnl, setup). Output: (1) 5 patterns I should be aware of, (2) the 3 trades that hurt the most and what setup they were, (3) my best-performing setup and my worst, (4) one rule I should add to my plan this week. Be direct. Don't soften the bad news.*

**Time saved:** 2-3 hours/week → 5 minutes to read. **Annual value:** ~120 hours.

### Agent 3: Position-sizing calculator

**What it does:** before every trade, the agent takes your account size, your risk %, and the volatility of the asset, and returns: share count, stop price, target price, risk-reward ratio.

**The prompt:**

> *I have an account size of $[X]. My risk per trade is [Y]%. The asset is $[Z] with an ATR of $[A]. Entry is $[E]. Output: (1) number of shares, (2) stop loss price, (3) target price, (4) risk-reward ratio, (5) dollar amount I risk. If the risk-reward is below 2:1, tell me to skip the trade.*

**Time saved:** 1-2 minutes/trade × 50 trades/month = 50-100 minutes/month. **Annual value:** ~15 hours + the trades you don't blow up on because you sized correctly.

### Agent 4: EOD recap + tomorrow's plan

**What it does:** at 4:30pm every weekday, the agent reads your trades, the day's news, tomorrow's economic calendar, and your watchlist. It writes a 1-page recap (what you did, what worked, what didn't) and a 1-page plan for tomorrow.

**The prompt:**

> *You are my evening assistant. Read my work today, the news that moved the market, and tomorrow's calendar. Output: (1) a 5-line recap (what I did right, what I did wrong), (2) the 3 things I'm watching tomorrow, (3) the 1 piece of news that could move my work, (4) my risk budget for tomorrow in dollars. Be honest. If I worked badly, say so.*

**Time saved:** 1-2 hours/day → 10 minutes to read. **Annual value:** ~300 hours.

### Agent 5: Compliance / post-trade ops

**What it does:** every Friday at 5pm, the agent reads your weekly fills, checks them against your risk rules, and emails you a compliance summary. Every violation flagged, every metric measured, every limit tracked.

**The prompt:**

> *You are a compliance officer. Read my weekly fill report and my risk rules: [paste rules]. Output: (1) every trade that violated a rule, with the rule and the date, (2) my maximum position size, (3) my maximum daily loss, (4) my current drawdown vs peak, (5) a flag if any metric is approaching my limits. If everything is clean, say so in one line.*

**Time saved:** 2-3 hours/week → 10 minutes to review. **Annual value:** ~120 hours.

**Total time saved across all 5 agents: ~1,150 hours/year.** That is roughly half of a full-time job's worth of time back, every year.

---

## The 3 things you actually need

You don't need a $500/month bot. You need 3 things:

1. **A paid LLM API key** ($20/month for ChatGPT Plus or $5-30/month for direct API access). The API is the engine.
2. **A spreadsheet or Notion to store the data** (free). Your inputs, your outputs, your rules. The data is the fuel.
3. **1 hour a day for 30 days** to set this up. Day 1: agent 1. Day 2: agent 2. By day 30, all 5 are running.

The wrong choice is to buy a $500/month "AI trading bot." The right choice is to spend 30 hours setting up the 5 agents that work for you for the next 5 years.

---

## The 5 guardrails (the part most "AI agent" articles skip)

Your agents are dumb. They'll loop. They'll hallucinate. They'll try to email 10,000 recipients if you let them. The 5 guardrails are how you sleep at night:

1. **Loop detector.** Hard cap on agent steps. If the agent has tried 10 things and still hasn't finished, kill it. The wrong choice is to let an agent run for 3 hours burning API credits.
2. **Schema validator.** The agent's output must match a fixed structure. If wrong, retry. If it can't fix it, abort. The wrong choice is to trust free-form output.
3. **Cost ceiling.** Cap your LLM spend at $20/month. The agent stops when it hits the cap. The wrong choice is to discover a $2,000 bill.
4. **Idempotency.** The same input produces the same output. Don't let the agent email the summary twice because you clicked "Run" twice. The wrong choice is to wake up to 5 duplicate emails at 3am.
5. **Audit log.** Every run writes a record: what it read, what it decided, what it sent. Review the log weekly. The wrong choice is to trust the agent without looking.

The 5 guardrails are the difference between a $20/month habit and a $2,000/month disaster. **Every agent you build needs all 5, every time, no exceptions.**

---

## The 12 workflows this pattern unlocks (beyond trading)

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

Pick the one that costs you the most hours. Build the agent. Move to the next. Same 5 guardrails, same 30-day build.

---

## Where the money actually comes from (a real answer)

You asked. Here's the honest answer: **Substack and Medium pay pennies. LinkedIn and your own course pay the bills.**

| Platform | How you make money | Milestone to first $100 | Best for |
|----------|--------------------|--------------------------|----------|
| **Substack** | Paid subscriptions ($5-10/month, you keep 90%) | 20 paid subs = $100/mo (3-6 months) | Recurring revenue + lead-gen |
| **Medium** | Per-read payout from a fixed monthly pool | Variable, $5-30 per 1K reads (1-3 months) | One-off viral posts; SEO long-tail |
| **LinkedIn** | No ads — you build authority, get DMs, sell your own course | 1 lead/week in 1-4 weeks | B2B / consulting / high-trust |
| **Your own course** (Gumroad, Teachable, your own site) | Direct sales at $47-497/course, 95% margin | 1-3 sales/week = $100-500 (2-8 weeks) | Highest LTV; you own the list |
| **YouTube** | AdSense ($2-8 per 1K views) + sponsorships | 1K-10K subs for $100/mo (6-12 months) | Long-tail discovery; SEO |

**The funnel that actually works for an AI teaching business in 2026:**

- **Days 1-30:** Post 3-5×/week on LinkedIn. Write 1 Substack article. Get to 100 LinkedIn followers. First 5 DMs from readers.
- **Days 31-60:** Get to 500 LinkedIn followers. 5 Substack articles. 20 paid Substack subs. First $100.
- **Days 61-90:** Launch the $97 course. 10-20 sales from LinkedIn + Substack = $1K-2K. First consulting client at $200-500/hr = $1K-3K. **Total: $2K-5K month 3.**

Substack is the top of the funnel. LinkedIn is the distribution. Your own course is the revenue. 1:1 consulting at $200-500/hr is the high-ticket backend. **The article's $ is in the leads it generates, not the reads it gets.**

---

## Your 30-day plan (the 5 agents, day by day)

| Day | Agent | Time | What you build |
|-----|-------|------|----------------|
| 1-3 | Pre-market research | 3 hours | News API + LLM prompt + cron job (5am daily) |
| 4-6 | Trade journal analysis | 3 hours | Your data CSV + LLM prompt + Sunday cron |
| 7-9 | Position-sizing calculator | 2 hours | Spreadsheet with the formula + LLM prompt |
| 10-12 | EOD recap + tomorrow's plan | 3 hours | Day's inputs + news API + LLM prompt + 4:30pm cron |
| 13-15 | Compliance summary | 3 hours | Fill report + risk rules + LLM prompt + Friday cron |
| 16-30 | Iterate, debug, refine prompts | 10 hours | Add the 5 guardrails; check the audit logs; tune the prompts |

After day 30, you have 5 agents that run for you every day. The agents don't sleep. They don't take weekends off. They don't argue with you about whether to size up.

You do.

---

## What this means for 2026

Here's the thesis: **the boring work is going away.** Not in 5 years. In 18 months. The person who automates their 5 boring workflows in 2026 has a 6-12 month head start on the person who waits for "AI to get good enough."

AI is already good enough. What's missing is **the prompt, the guardrails, and the habit.** The person who writes the prompt, sets the guardrails, and runs the agent on a cron job wins — not because the agent is smart, but because the agent is **disciplined** in a way humans aren't.

The 5 workflows above are a template. **Pick your 5 boring workflows. Write the prompt. Set the guardrails. Run the agent on a cron job. Iterate weekly.** That's the whole game.

The agents don't make you money. They give you the time and the discipline to make money yourself.

That's the whole game.

— Vishnoi

---

**Sources for the numbers in this article:**

- [Track360 — Best Prop Firms 2026: Definitive Ranking](https://track360.io/blog/best-prop-firms-2026-definitive-ranking) (industry context for the trading example)
- [PropFirmScope — Best Prop Trading Firms 2026](https://propfirmscope.com/best/best-prop-firms-2026)
- [Write • Build • Scale — Medium vs Substack (real subscriber math, 2025)](https://writebuildscale.substack.com/p/medium-vs-substack-comparison)
- [Better Marketing — Medium vs Substack vs LinkedIn](https://bettermarketing.pub/best-platform-for-writers-to-make-more-than-1000-per-month-medium-vs-substack-vs-linkedin-a16c6b91c56b)
- [Mark Schaefer — Is it time to monetize your audience through Substack?](https://www.linkedin.com/pulse/time-monetize-your-audience-through-substack-mark-schaefer-jmhqe)

*This article is the Substack version of L10.1 in the [FDE course](https://github.com/your-repo/course/ai-fde/phase-6-interview-prep/generative-ai/companion-courses/intro-to-ai-agents/s10-ai-in-trading/). The course version has the 200-line TradingAgent class, the 7 ingredients, the 5 guardrails, and the 8-section template.*
