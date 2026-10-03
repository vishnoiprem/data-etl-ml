# Ownership and Conflict Resolution (0→1 Data Initiative, Prioritization, Cross-Functional Leadership)

## 1. Simple way to think
- "0→1" is the magic phrase at Meta. It means: there was nothing, then you built it, now it exists and people depend on it. The interviewer wants to know you can *invent*, not just *maintain*.
- Ownership is not "I stayed late." It's "I made decisions no one asked me to make, and I'd make them again."
- Cross-functional leadership is harder than people-management leadership: you can't hire, fire, or review. You lead through artifacts, reputation, and clarity.
- Prioritization is the silent test. Every 0→1 story has 10x more possible work than time. The interviewer is asking: do you know how to choose?
- The hidden competency: **narrative control**. Senior DEs who ship 0→1 also write the memo that makes leadership fund it.

## 2. Interview write-up (how to solve it)

**STAR — 0→1 + cross-functional + prioritization + conflict:**
- **Situation:** I noticed our org's experiment-analysis pipeline was a Frankenstein: 3 different Python scripts run by 4 analysts in 4 notebooks, taking 2 days per experiment, with no shared definitions of "user" or "exposure."
- **Task:** Build a unified experimentation data product from scratch — owned by no one, depended on by everyone. No team was asking for it; I had to make the case.
- **Action:**
  1. **Built the case (week 0–2).** I wrote a 2-pager quantifying the cost: ~40 engineer-days/year in duplicated work, 3 conflicting "active user" numbers in the board deck. I got my director to back me for 0.5 FTE of my time.
  2. **Took ownership of the design.** I drafted the data contracts (event taxonomy, user-resolution rules, exposure semantics) and shopped them to 6 stakeholders — including the senior analyst who'd been doing it his way for 3 years (a real conflict).
  3. **Resolved the conflict with the senior analyst.** He wanted retroactive compatibility with his existing notebooks. I proposed a shim layer that translated old → new for 90 days. He got to keep his workflow; I got the canonical pipeline. He became one of my strongest advocates.
  4. **Prioritized ruthlessly.** Cut the v1 scope to: exposure tables, 1 user-resolution function, 3 reusable metric templates. No backfill UI, no Grafana, no SLA dashboards — those came in v2 after adoption.
  5. **Drove cross-functional adoption.** Ran 3 brown-bag sessions, wrote a "migration in 30 minutes" guide, and personally migrated 1 of the 4 analyst teams to unblock the others.
- **Result:** v1 shipped in 10 weeks. 2 of 4 analyst teams migrated within 3 months. Experiment turnaround time: 2 days → 4 hours. The senior analyst and I co-presented at our internal data summit. The 2-pager was reused (with my blessing) by 2 adjacent teams. Director cited it in the org's annual review.

**What makes this answer strong:**
- Real 0→1: there was nothing, then there was something, then people depended on it.
- Conflict resolved through *enlargement* (the shim) rather than competition — shows maturity.
- Quantified cost of the status quo *before* the build (a Meta-style "is the problem worth solving?" check).
- Cross-functional leadership via artifacts (2-pager, brown-bags, migration guide), not authority.
- Explicitly named what got cut from v1 — prioritization is a feature.

## 3. Best optimized solution
Polished version condenses to: *"I saw a cost no one had quantified, wrote the case, designed the contracts, found a shim to neutralize the biggest blocker, cut scope by half, and migrated the first team myself."* Reflection: *"0→1 work is mostly narrative work — the engineering is the easy part. If you can't write the memo, the system won't get built."*

**What to prepare before the interview**
- A genuine 0→1 story with a "before/after" — what didn't exist before, what exists now, who depends on it.
- A 1-pager you've written for leadership (bring it to the interview mentally — be ready to summarize it).
- A story where you cut scope, including what was *rejected* and why.
- A story where you took ownership of something outside your team's charter (a hallmark of senior DEs).

**Variations the interviewer might push on**
- *"What would you have done if your director hadn't backed you?"* — Shows whether your ownership is contingent on permission. Have a real answer: e.g., "I would've built a weekend prototype with one analyst as a beachhead."
- *"How did you decide what to *not* build in v1?"* — Name the framework (e.g., "Adoption first, ergonomics later" or "Unblock the most blocked team first"). Avoid "it felt right."
- *"Tell me about a cross-functional project that failed."* — Have a real failure. Frame as: what you learned about stakeholder mapping, about the limits of memo-driven influence, or about under-investing in change management.

**Red flags to avoid:** 0→1 stories where "I" actually means "I joined a team that was already doing it"; scope-cutting with no reasoning; conflict stories where the "other side" is unnamed or made to look bad; cross-functional "leadership" that's really just stakeholder-management theater; stories without a quantified "before"; refusal to admit the 0→1 took longer or hit more friction than you expected.