# CS-07 (Google) — The Alphabet 3-C conflict: Pichai wants 10x AI, the CFO wants capex discipline, Kurian wants Cloud margin

> **Mapping:** Original CS-07 (3-C conflict). Retargeted to the Alphabet cast.
> **Goal:** 30 minutes. Mediate a 3-C conflict between Sundar (CEO), the CFO, and Thomas Kurian (Cloud CEO).

## The brief

You are 6 months into the Head of Data role. Three C-level peers have a conflict that you have to resolve (or escalate). The board is watching.

**The conflict:**
- **Sundar Pichai (CEO):** "Ship 10x AI in production in 12 months. The board wants this. The Gemini cadence is the strategy."
- **CFO:** "Cut the capex growth. $75B 2025 is unsustainable. Show me the ROI on every AI dollar."
- **Thomas Kurian (Cloud CEO):** "Cloud margin is the metric. The AI infra is in Cloud. I need the cost per Gemini query to drop 50%."

Each C is right. Each C is also wrong — they don't see the others' constraints.

**Your task:** Mediate. Find a path that:
- Ships visible AI at 10x (the CEO's win)
- Cuts capex growth or proves ROI (the CFO's win)
- Drops cost per query 50% (Kurian's win)
- Doesn't break the data team or the federated BU relationships

You have 30 minutes in front of the 3 Cs. They will challenge every trade-off.

## The structure (30 min)

| Section | Time | What to say |
|---|---|---|
| Framing | 3 min | Name the conflict; reframe as joint problem |
| Diagnosis | 5 min | What each C sees that the others don't |
| Proposal | 10 min | The path that hits all three |
| Trade-offs | 7 min | What each C gives up |
| Asks | 5 min | What each C commits to |

## Solution sketch (do not copy — internalize and re-speak)

**Framing (3 min).** "We have three legitimate constraints, not three competing priorities. Let me name each, then propose a path that hits all three."

**Diagnosis (5 min).**
- Pichai: 10x AI because the board mandate is a clock. Hidden cost: shipping insecure AI is worse than shipping late AI.
- CFO: capex discipline because the macro is tightening. Hidden cost: cutting the foundation cuts the AI ROI.
- Kurian: Cloud margin because Cloud is the business. Hidden cost: 10x AI without cost-per-query reduction kills Cloud margin.

**Proposal (10 min).**

| Constraint | Path |
|---|---|
| Pichai — 10x AI in 12 months | Ship 5 cross-plane AI in 12 months (not 10x in count, but 10x in capability). Scope: AI Overviews expansion, Performance Max optimization, Gemini 2.5 eval-driven releases, Cloud AI workloads, YouTube creator analytics. |
| CFO — capex discipline | Cut $XM in non-AI capex; defer 1-2 non-AI Cloud projects; consolidate 2 internal systems; prove ROI per Gemini version. |
| Kurian — cost per Gemini query down 50% | Cost optimization roadmap: model distillation, inference cost reduction, reserved capacity, spot for batch. Target: 50% drop in 9 months. |

The math: 5 cross-plane AI × `[CONFIRM: $XM revenue / margin each]` = $XM revenue. Cost per query -50% × `[CONFIRM: Gemini query volume]` = $XM Cloud margin. Net of capex cut: $[CONFIRM: net positive ROI]`.

**Trade-offs (7 min).**
- Pichai gives up: 10 AI in production → 5 in production. The 10x claim is reframed from count to capability.
- CFO gives up: $75B → $[CONFIRM: $XM with the cuts]. Some capex growth remains; the ROI must prove it.
- Kurian gives up: 12-month timeline → 9-month timeline for the cost reduction. The cost optimization cuts some model capabilities.

**Asks (5 min).**
- Pichai: back the 5-AI scope with the board; defend the capability-over-count reframe.
- CFO: approve the capex cuts; back the ROI tracking per AI project.
- Kurian: own the cost-per-query reduction; sign off on the cost optimization roadmap.

**Q&A — be ready for:**
- "What if the board doesn't accept 5 AI?" — We go with 3 AI on a smaller scope; the capability claim is harder to defend.
- "What if the capex cuts slip?" — Phased plan; first $XM in 6 months, second $XM in 12.
- "What if the cost optimization misses the 50% target?" — Cut scope further; we don't ship unprofitable AI.
- "What if a BU head still pushes for 10 AI?" — Communicate the trade-off; the 5-AI scope is the path; the 10-AI scope is the wish.

## Watch for when you re-listen

- **Did you validate each C first?** If they don't feel heard, they won't sign off.
- **Did you reframe as joint problem?** If the room thinks it's "Pichai vs. CFO," you've lost.
- **Did you name every trade-off?** A proposal without trade-offs is a wish.
- **Did you end on time?** If you run over, the Cs conclude you can't manage complexity.

---

**Source:** Adapted from original CS-07 + Google case-study brief.