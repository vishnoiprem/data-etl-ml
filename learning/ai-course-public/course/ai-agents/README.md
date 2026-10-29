# AI Agents — Flagship Course

> **Promise:** Before you ship a single agent, know if the math works. This course gives you a runnable ROI formula, a 1000-cycle proof, and a watchdog autopilot that re-proves it forever.

---

## Who this is for

| Audience | Start with | Time to first win |
|---|---|---|
| SMB owner in SG / TW / VN / CN with $0-50/mo LLM budget | [Lesson 1: The ROI formula](#lessons) | 15 min |
| AI engineer building production agents | [L4: Production patterns](#lessons) | 45 min |
| Course author / consultant pitching AI agent work | [L5: 1000-cycle review](#lessons) | 20 min |
| Executive who needs a one-pager | [results/1000_cycle_review_*.md](results/) | 5 min |

## What you'll build

1. **An ROI formula** for any agent deployment — 6 inputs, 1 cost, 1 monthly $ answer.
2. **A 4-criteria use case rubric** to filter "build this" from "skip this" before writing code.
3. **A 1000-cycle review** that runs the formula 1000 times against realistic Asian SMB ranges and reports the distribution.
4. **A watchdog autopilot** that re-runs the review every 30 min and writes a fresh markdown report.
5. **A reproducible truth** — same seed, same inputs, same output. No "trust me, it worked on my machine."

## Lessons

| # | Title | What it is | Status |
|---|---|---|---|
| L1 | [The ROI formula](lessons/01-roi-formula.md) | The 4 use case criteria + the 6-knob formula + 3 worked examples. **Run it:** `python3 lessons/01-roi-formula.py` | 📝 drafted |
| L2 | The 7 ingredients | Tool registry, mock LLM, structured observability, idempotency, cost tracker, loop detector, audit log. See [course/ai-fde/.../intro-to-ai-agents/s02](../ai-fde/phase-6-interview-prep/generative-ai/companion-courses/intro-to-ai-agents/s02-essential-ingredients/) | 📤 published (elsewhere) |
| L3 | The 5 guardrails | Schema validator, cost ceiling, kill switch, output sanitizer, time-box. See [course/ai-fde/.../intro-to-ai-agents/s02](../ai-fde/phase-6-interview-prep/generative-ai/companion-courses/intro-to-ai-agents/s02-essential-ingredients/) | 📤 published (elsewhere) |
| L4 | Production patterns | The patterns from `lesson-9-6-production-agents` recast for this course. See [course/practice/level-5-agents/lesson-9-6](../practice/level-5-agents/lesson-9-6-production-agents.md) | 📤 published (elsewhere) |
| L5 | [1000-cycle review](notebook.ipynb) | The executable notebook. 1000 random SMB scenarios, P50/P05/P95, stability sweep, verdict. **Run it:** `jupyter nbconvert --to notebook --execute notebook.ipynb --output notebook.ipynb` | 📝 drafted |

## Quick links

| What | Where |
|---|---|
| The formula (canonical) | [code/agent_roi.py](code/agent_roi.py) |
| The 1000-cycle runner | [code/run_1000_cycles.py](code/run_1000_cycles.py) |
| The tool registry + cost tracker | [code/tools.py](code/tools.py) |
| The lesson code (L1) | [lessons/01-roi-formula.py](lessons/01-roi-formula.py) |
| The lesson doc (L1) | [lessons/01-roi-formula.md](lessons/01-roi-formula.md) |
| The lesson notebook (L1) | [lessons/01-roi-formula.ipynb](lessons/01-roi-formula.ipynb) |
| The headline notebook (L5) | [notebook.ipynb](notebook.ipynb) |
| The autopilot | [autopilot/run_autopilot.sh](autopilot/run_autopilot.sh) |
| Latest 1000-cycle results | [results/latest.json](results/latest.json) |
| Latest 1000-cycle report (human) | [results/1000_cycle_review_*.md](results/) |

## The headline number

```bash
cat results/latest.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'P50=\${d[\"median_roi\"]:+.0f}/mo  P05=\${d[\"p05_roi\"]:+.0f}/mo  %pos={d[\"pct_positive\"]:.1%}')"
```

| Metric | Current value | What it means |
|---|---:|---|
| Median (P50) monthly ROI | **+$239** | The typical SMB nets $239/mo after agent cost |
| P05 (downside) | **+$0** | Even in the worst 5% of scenarios, the agent nets ≥ $0/mo |
| P95 (upside) | **+$965** | Best 5% of scenarios net $965/mo |
| % positive | **95.1%** | 95% of realistic SMB scenarios are net-positive |
| %>= 3× payback | **63.1%** | 63% of scenarios pay back ≥ 3× the agent cost |
| Cycles / second | **285,638** | Re-runs the entire review in 4 ms |

**Verdict:** **PASS.** The formula is robust. Median positive, downside is not catastrophic, stable across seeds.

## Run it yourself

```bash
# 1. The lesson (15 min, no setup)
python3 lessons/01-roi-formula.py

# 2. The headline proof (20 min, no setup)
jupyter nbconvert --to notebook --execute notebook.ipynb --output notebook.ipynb

# 3. The 1000-cycle CLI (1 sec, no setup)
python3 code/run_1000_cycles.py

# 4. The watchdog autopilot (forever, every 30 min)
bash autopilot/run_autopilot.sh
```

## What this course is NOT

- **NOT** a survey of agent frameworks (LangChain, CrewAI, AutoGen, LangGraph). We use plain Python + a mock LLM.
- **NOT** a tutorial on prompt engineering. We assume you can already write a 3-line prompt.
- **NOT** a vendor pitch. The `agent_cost_usd` range is $10-100/mo and you can hit it with any provider.
- **IS** the math-first, distribution-aware, autopilot-verified ROI proof for an agent deployment.

## Why this matters

Most "AI agent" courses sell you a framework. This one gives you a formula and a watchdog. The formula tells you **what the answer is in dollars**. The watchdog tells you **if the answer changed**. Together they're the difference between "I built a thing" and "I shipped something that's worth money."

---

*Last updated: 2026-10-14*
*License: MIT*
