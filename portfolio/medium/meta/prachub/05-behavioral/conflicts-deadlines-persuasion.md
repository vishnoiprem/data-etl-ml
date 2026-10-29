# Conflicts, Deadlines, and Persuasion (DE Leadership Behavioral)

## 1. Simple way to think
- Data Engineers at Meta frequently sit at the intersection of product, infra, and analytics — i.e., **involuntary diplomats**. These questions test whether you can move people who don't report to you.
- Persuasion without authority is the core skill: you don't own the consumer of your data, you don't own the producer of an upstream event, you don't own the analyst's dashboard. Yet you must ship.
- Conflict stories should have a **named** dissenting party, a *real* disagreement (not "we disagreed on color"), and a resolution that left both sides feeling heard.
- Deadline stories must show **honest tradeoffs**, not heroic suffering.
- The strongest signal: you changed your own mind based on new information. Interviewers want to see updateability.

## 2. Interview write-up (how to solve it)

**STAR — Conflict + persuasion:**
- **Situation:** During a payments-data quality initiative, I discovered that ~3% of transactions were being double-counted downstream because two upstream services emitted events with subtly different schema versions. The analytics team had built their revenue dashboards on top of the buggy data for ~8 months.
- **Task:** I needed to (a) fix the root cause (service owners), (b) decide if we re-process historical data (Finance cared), and (c) tell the analytics team their numbers had been wrong. Three stakeholders, three different pressures.
- **Action:**
  - **Mapped the conflict.** I scheduled a 30-min meeting with the analytics lead and the two service owners separately first — never ambushed people in a group.
  - **Influenced without authority.** I built a one-page impact analysis showing $X of misreported revenue, attached a reproducible SQL query, and proposed two paths: "quick fix (no backfill, dashboards reannotate, ships in 1 week)" vs. "full fix (backfill, ships in 6 weeks)." I let each owner pick.
  - **Persuaded Finance on partial backfill:** Finance wanted full historical correction; the service owners pushed back on cost. I proposed a middle path — backfill the last 90 days (covered 92% of the impact at 18% of the compute cost). Finance accepted after I showed the math.
  - **Handled the analytics team's trust hit:** I told them first, showed them the fix, and asked what they needed to communicate to their stakeholders. I joined one of their meetings to absorb the questions with them.
- **Result:** Quick fix shipped in 6 days. 90-day backfill shipped 3 weeks later. Revenue dashboards re-annotated. The analytics lead later nominated me for a cross-team award, citing the way I'd handled the disclosure.

**What makes this answer strong:**
- Real, technical conflict — not "personality clash" fluff.
- Shows persuasion *technique*: pre-meetings, written analysis, two-options framing, math-based compromise.
- Treats stakeholder trust (analytics team) as a first-class concern, not a footnote.
- Quantified: 3% error, 92% impact at 18% cost — the kind of numbers an interviewer can latch onto.

## 3. Best optimized solution
Polished version frames it as a *system*: *"When I have no authority, I write a one-pager with the math, propose two options, let the stakeholder pick, and pre-meet everyone."* Reflection: *"Most engineering conflict is information conflict; my job is to reduce information asymmetry before negotiating positions."*

**What to prepare before the interview**
- A persuasion story where you changed someone's mind using *data*, not seniority.
- A conflict story where you **conceded** something real (the strongest signal of updateability).
- A deadline story where you delivered under promise but said "no" to something along the way.
- A time you escalated — and a time you didn't (knowing when *not* to escalate is underrated).

**Variations the interviewer might push on**
- *"What do you do when the data says one thing and your stakeholder insists on another?"* — Show how you investigate first (is the data right? is the stakeholder using outdated assumptions?). Never just defer, never just bulldoze.
- *"Tell me about a time you had to influence someone more senior."* — Pick a story with genuine power asymmetry (skip-level, VP). Show the technique: bring them a decision, not a problem.
- *"When do you escalate a conflict?"* — Have a clear rule (e.g., "When the issue is ethics, safety, or a commitments I've made to my team"). Don't say "I always try to resolve it myself first" — sounds like someone who lets things fester.

**Red flags to avoid:** Conflict stories where you "won" and the other party sounds incompetent; persuasion stories that lean on title/relationship ("my skip-level backed me"); deadline stories framed as heroic suffering with no tradeoff acknowledged; "I don't really have conflicts" (means you avoid them, which is its own red flag); inability to describe what you conceded.