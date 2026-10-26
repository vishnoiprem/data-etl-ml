# Meta L6 On-Site — Ownership & HR Round Prep Guide

> **Role:** L6 AI-Native Data Engineer
> **Round 5 of 5:** Sr Ownership / HR behavioral (30 min)
> **Companion to:** `META_L6_STUDY_GUIDE.md` and `meta_l6_onsite_mock.ipynb`

This guide turns Round 5 (Ownership) into a rehearsable interview. Read it, write out your STAR answers, then drill them with a friend.

---

## 1. Meta's Ownership Value — In Depth

### 1.1 What "Ownership" actually means at Meta

Meta's 5 values (verbatim):

1. **Move Fast**
2. **Be Bold**
3. **Be Open**
4. **Build Social Value**
5. **Ownership**

Ownership at Meta is **not** "I owned this Jira ticket." It is a layered competency. Interviewers score you on each layer:

| Layer | Definition | L4 signal | L5 signal | **L6 signal (target)** |
|------|-----------|-----------|-----------|------------------------|
| **End-to-end** | Took a problem from ambiguous to shipped, including the messy parts | Owned a component | Owned a project | Owned a product surface / system area |
| **Beyond scope** | Picked up things no one asked you to do | Helped when asked | Volunteered on adjacent problems | Defined the problem others worked on |
| **Outcome focus** | Cared about user/business impact, not activity | "I shipped X" | "X moved metric Y by Z%" | "I defined metric Z because none existed, then drove it from N→M" |
| **Tough calls** | Escalated correctly, handled conflict, made decisions under pressure | Avoided conflict | Negotiated tradeoffs | Made calls with incomplete data, took the heat, defended the decision |
| **Durability** | Left the system better than they found it | Wrote code | Added tests | Wrote runbooks, set SLOs, instrumented dashboards, prevented recurrence |
| **Mentorship & leverage** | Raised the bar for the team | Reviewed code | Mentored 1-2 | Multiplied output of a sub-team; defined how others work |

**The L6 ownership question is always:** *"Did you leave the system better than you found it? Did you define the problem? Did you make the call no one else wanted to make?"*

### 1.2 How interviewers actually assess it

HR/Ownership interviewers at Meta are typically trained on the **"CAR" loop** (Context → Action → Result) layered on top of STAR. They listen for:

- **"I" vs "we"**: real ownership stories use "I" for the decision, "we" for the work. If every sentence is "we", they probe harder.
- **Specificity**: vague stories ("improved the system") are downgraded. They want tool names, metric numbers, time windows, dollar amounts.
- **The ugly middle**: do you skip to the result, or do you describe the hard part? Ownership = describing the part where you had to make a call.
- **Self-awareness**: do you mention what you'd do differently? What tradeoffs you accepted?
- **Anti-patterns**:
  - "I told my manager and they decided" → not ownership
  - "We formed a committee" → diffusion
  - "I waited for requirements" → passivity
  - "It was a team effort" (without naming your specific decision) → L4 signal

### 1.3 Common ownership interview questions

These are the exact question shapes you'll see:

1. **"Tell me about a project you owned end-to-end."** (The classic opener — tests all 6 layers)
2. **"Describe a time you took on something beyond your defined scope."** (Tests the "beyond scope" layer)
3. **"Tell me about a time you disagreed with your manager."** (Tests tough calls + Be Open)
4. **"When did you decide to escalate vs. handle something yourself?"** (Tests judgment, calibration)
5. **"Tell me about a time you had to make a decision with incomplete information."** (Tests Move Fast + ownership)
6. **"Describe a situation where you had to influence without authority."** (Tests leverage, cross-functional)
7. **"Tell me about a time you held the on-call pager / dealt with a 2am page."** (Tests durability)
8. **"What's a system or process you inherited and made significantly better?"** (Tests end-to-end + durability)
9. **"Tell me about a time you pushed back on a project you thought was the wrong priority."** (Tests boldness + ownership)
10. **"Describe a time you failed. What did you learn? What did you change?"** (Tests self-awareness)
11. **"Tell me about the most ambiguous problem you've solved. How did you even know it was a problem?"** (Tests "define the problem")
12. **"Have you ever had to stop a project? How did you decide?"** (Tests tough calls)

---

## 2. General Meta HR / Behavioral Questions

The first 5 minutes of Round 5 and the last 5 minutes. Master these cold.

### 2.1 "Tell me about yourself" (2 minutes, max)

Use the **3-layer pitch** (from the study guide) but tailor the third layer to ownership:

```
1. WHO I AM (10s)       → Title + years + stack one-liner
2. WHAT I'VE SHIPPED (60s) → 2 projects with METRICS
3. WHY THIS ROLE (30s)   → Why Meta + why this team + what I'll OWN
```

**L6 answer template** (memorize, then personalize):

> "I'm a Data Engineer who's gone AI-native. [N] years building data platforms — Kafka, Flink/Spark, Postgres, vector DBs. Last [M] years I pivoted: built RAG pipelines, eval harnesses, agent memory systems. I own pipelines end-to-end — ingestion, data quality, LLM eval, the whole loop.
>
> Most recent win: I owned [system X]. It was [scope/ambiguity]. I defined the metric [Y], shipped in [Z weeks], moved [business outcome] from [A] to [B], and left a runbook that prevented recurrence — zero incidents in 6 months.
>
> I'm looking for a role where I own a system surface — not just ETL, but prompts, embeddings, eval — at Meta's scale. Specifically, [team name]'s work on [X] is exactly the problem space I want to take end-to-end ownership of."

### 2.2 "Why Meta?"

**Don't say:** "Meta pays well / great brand / free food." **Do say:** one of:

- A product you genuinely use and want to work on ("I use WhatsApp daily in Portuguese; the ranking team's work directly affects my family")
- A technical bet Meta has made that you want to learn from ("Llama and PyTorch are public bets on open AI; I want to see how internal data systems feed those")
- The scale itself ("1B users, 1B traces/day — there's no school for that, only Meta")
- A founder/Journey you admire ("Brocker's 'Data Systems that Scale' shaped how I think about SCD2 and bounded fanout")

**Pair with a specific team:** "I'm interviewing for the GenAI Infra team because [their recent post on X / paper / open-source release] is the problem space I want to own."

### 2.3 "Why this role? / Why L6?"

> "I've been doing [scope] for [N] years. I want a role where owning [X surface] is the job, not something I do on top of my day job. L6 is the right level because I've already led [project] end-to-end at [smaller scale], and I'm ready to do it at Meta's scale and on a surface others consume."

### 2.4 "Where do you see yourself in 5 years?"

**Bad answer:** "At Meta, growing into management."
**Good answer:** Pick one of these trajectories and be specific:

- **IC track:** "L7 staff engineer, owning a multi-team data/AI surface. I want to be the person teams come to for [embeddings/eval/RAG platform] architecture."
- **Tech lead:** "I want to be the tech lead on a [platform] team. My strength is right now: I can write code, define metrics, run an incident, and write the postmortem. I want to spend 5 years scaling that to a team of 6-8."
- **Hybrid:** "I want to stay close to the code but have product surface ownership. I like being the person who defines the problem and ships the first version."

### 2.5 "Strengths?"

Use **strength + proof + cost**:

> "My strength is **end-to-end ownership**. Proof: [specific project where you owned ambiguous → shipped]. The cost of that strength is that I sometimes over-function — I'll pick up work others could do. I've learned to write things down so others can take them, instead of doing them myself."

### 2.6 "Weaknesses?"

**Rule:** Real weakness, with the *system* you've built to mitigate it.

> "I move fast on technical decisions but slower on people decisions — early in my career I avoided 1:1 conflict. Two years ago I forced myself to give weekly written feedback and run skip-level 1:1s. It's not natural for me, but the system works."

**Don't say:** "I'm a perfectionist" (overused), "I work too hard" (bragging).

### 2.7 "Conflict resolution"

Frame as **data, not opinions**. The L6 answer:

> "I separate the person from the problem. I write down what each side is actually optimizing for, find the metric both sides agree on, and decide based on that. If we still disagree, I escalate with a written doc — 1 page, options + recommendation — so the decision is data-driven, not political."

### 2.8 "Tell me about a failure"

Use **CAR + lesson + system change**:

> "I shipped a feature without defining the success metric. We celebrated for a month, then realized it didn't move the business KPI. **Lesson:** I never start work without writing 'how will I know this worked' first. **System change:** my team now requires a one-line success metric in the PR description for every non-trivial change."

### 2.9 "Dealing with ambiguity"

> "I write the problem down. Specifically: I send a doc with three sections — context (what I know), unknowns (what I don't), and the smallest experiment that resolves the unknowns. Then I propose a default, ask for objections in 48 hours, and start building. Move Fast means default-to-action with a small, reversible first step."

### 2.10 "Working in cross-functional teams"

> "I bring the data and the metric. When DE and ML disagree on data quality, I propose a data contract: ML writes the gold schema, DE commits to freshness + schema SLAs, both are checked in CI. Conflict becomes a passing/failing test, not a meeting."

### 2.11 "Tight deadlines"

> "I cut scope, not quality. I split deliverables into P0 (must ship) and P1 (can ship next sprint). I tell stakeholders early: 'we can ship A and B by Friday, or A, B, C by next Friday — you pick.' Move Fast means shipping the smallest valuable thing on time, not the whole thing late."

---

## 3. Meta's Culture & Values — How They Show Up

### 3.1 The 5 values, decoded

| Value | What it really means | Anti-pattern | Interviewer probe |
|-------|---------------------|-------------|------------------|
| **Move Fast** | Bias to action; small reversible steps; ship to learn | Analysis paralysis; "perfect plan first" | "Tell me about the fastest you've shipped something — what did you skip?" |
| **Be Bold** | Take the big swing even if 50/50 | Play it safe; incremental-itis | "Tell me about a moonshot you proposed that didn't work" |
| **Be Open** | Default to transparency; share context widely; disagree directly | Information as power; politics | "Tell me about a time you gave someone hard feedback" |
| **Build Social Value** | Work that matters at Meta's scale; impact >1B people | Vanity metrics; local optimization | "How do you know your work mattered?" |
| **Ownership** | End-to-end; beyond scope; outcome focus; tough calls; durability | Hand-offs; "not my job"; waiting for requirements | All Round 5 questions |

### 3.2 Hacker Way phrases you'll hear

These are slogans from the original Meta engineering culture. They show up in interviews:

- **"Done is better than perfect"** — they want to see you've shipped imperfect things on time and iterated.
- **"Code wins arguments"** — when there's a debate, prototype both and let the data decide. Don't debate in meetings.
- **"Move fast and break things"** — they've softened this externally, but internally the spirit is: ship, learn, fix in prod.
- **"The Hacker Way"** — build it yourself first, don't wait for a vendor or a separate team.
- **"Be a fox, not a hedgehog"** (loosely) — have many small bets, not one big one.

### 3.3 Cultural trap questions and how to handle them

**Q:** "What's the biggest risk you've ever taken at work?"
**Move Fast + Be Bold answer:** "I shipped to 5% of users without manager approval because the data was clear and the rollback was 30 seconds." *Then explain the guardrails.*

**Q:** "Tell me about a time you disagreed with your manager publicly."
**Be Open answer:** "Yes. I wrote a one-pager with the data, sent it to my manager and their manager, asked for 48 hours of objections, then started. My manager was initially against it, but the data convinced them, and the project shipped."

**Q:** "Have you ever built something nobody asked for?"
**Be Bold answer:** "Yes. I built [X] in 20% time because [signal]. It became [outcome]."

---

## 4. Data / ML-Specific Behavioral Framing

For your L6 AI-Native DE role, every ownership story should land on **at least one** of these surfaces. Use this checklist when prepping:

### 4.1 The data/ML ownership story surfaces

| Surface | Story angle | Example metric |
|---------|-------------|----------------|
| **Data pipeline** | You owned ingestion end-to-end | Freshness SLA: 5min → 90s; cost: $X/mo → $Y/mo |
| **ML model** | You owned a model in prod (training → serving → monitoring) | AUC, p95, satisfaction |
| **ETL migration** | You migrated a system without downtime | $X saved, latency reduced, zero incidents |
| **Production incident** | You were on-call, owned the rollback and the postmortem | MTTR, recurrence prevention |
| **Stakeholder management** | You owned the relationship with ML/PM/Analytics | Adopted by N teams, X% satisfaction |
| **Eval / data quality** | You built the eval harness / data contract | Caught N regressions pre-prod |
| **Cost / efficiency** | You re-architected to save $X | $X/mo savings, latency same |
| **Cross-team platform** | You built the platform N teams now depend on | N consumers, NPS, time-to-first-pipeline |

### 4.2 The data/ML ownership story library

Pick **3-4 of these and write full STARs now** before the mock:

1. **"I owned a data pipeline that broke at 2am."** (incident + runbook + SLO)
3. **"I owned the eval dataset for our RAG system."** (defined the problem, built gold set, drove A/B)
4. **"I owned the migration from [old system] to [new]."** (cutover plan, zero downtime, cost savings)
5. **"I owned the data contract between DE and ML."** (conflict → schema → CI check)
6. **"I owned the prompt versioning system."** (built the versioned prompts table, A/B framework)
7. **"I owned the on-call rotation and reduced pages by 80%."** (runbook, dashboards, alerts)
8. **"I owned the chunking strategy for our RAG."** (defined metric, A/B tested, shipped)
9. **"I owned the cost optimization that saved $X/mo."** (specific numbers, specific decision)
10. **"I owned the cross-team rollout to N consumer teams."** (stakeholder mgmt + adoption metric)

### 4.3 Production incident stories — the L6 template

This is the single highest-leverage story to prepare. Most L6 candidates have at least one; if you do, nail it.

```
S: At [time] on [date], [user-visible symptom]. [N] users affected, [M$] revenue at risk.
T: No runbook. On-call was paged. Manager asked "what happened?"
A (the L6 part):
  1. I owned the decision to roll back vs. fix forward. Decision: rollback because [reason in <10s].
  2. I rolled back in [X min] (named the tool, the command, the page).
  3. I wrote the postmortem in 24h (timed, blame-free, action items with owners and dates).
  4. I owned [N] of the [M] action items personally.
  5. I built the system that would have caught this: [dashboard / alert / test / SLO].
R: 
  - Time-to-detect: [before] → [after]
  - MTTR: [before] → [after]
  - Recurrence: zero in [N months]
  - Runbook is now team standard
```

---

## 5. STAR / CAR — The Answer Structure

### 5.1 STAR basics

- **Situation** (10% of time) — context, who, what, when
- **Task** (5%) — your specific responsibility / what you had to own
- **Action** (60%) — what YOU did, specifically (tools, decisions, tradeoffs)
- **Result** (25%) — quantified outcome + what you left behind

### 5.2 CAR (Context → Action → Result) — Meta's preferred variant

Used in HR rounds. Compresses S+T into Context, spends more time on Action.

### 5.3 The L6 STAR upgrade

Standard STAR is **task-completion storytelling**. L6 STAR is **decision-making + system change**:

```
Standard STAR:  "We had a problem. I did X. We fixed it. The result was Y."
L6 STAR:        "We had a problem (define it). I decided to do X over alternative Y 
                 because [reason]. The result was [metric]. I then built [system/runbook/
                 dashboard/SLO] so this couldn't happen again. That system is now [used 
                 by N people / standard / adopted]. The metric moved from A to B."
```

### 5.4 The "I vs We" rule

- **"We"** = collaborative work (build, design, debug together)
- **"I"** = your specific decisions (chose X over Y, escalated at this point, decided to ship vs. wait)

If you never say "I decided", your story sounds like L4 collaboration, not L6 ownership.

### 5.5 Answer length budget (for a 5-min answer)

| Section | Time | Words |
|---------|------|-------|
| Context | 30s | 80-100 |
| Decision/Task | 15s | 40 |
| Action | 3min | 350-400 |
| Result + prevention | 1min | 150 |
| What I'd do differently | 15s | 50 |

---

## 6. Questions to Ask the Interviewer (End of Round 5)

The last 3 minutes are yours. Use them. Strong questions signal ownership thinking.

### 6.1 Ownership / culture questions

1. **"How does this team define ownership? Is there an on-call rotation, and how often do engineers rotate?"**
   → Tests whether the team actually practices the value, not just preaches it.

2. **"When something breaks in prod at 2am, what's the typical MTTR and who's accountable?"**
   → Signals you expect to be on-call and care about operational excellence.

3. **"Can you give me an example of someone on this team who took end-to-end ownership of something hard? What was the outcome?"**
   → Tells you what the bar actually looks like in practice.

4. **"What's the last system someone on this team left better than they found it?"**
   → Same as above, but for durability — Meta cares deeply about this.

5. **"How does the team handle disagreements between DE and ML on data quality?"**
   → For an L6 DE, this is a daily reality. If they say "we have meetings", that's a red flag — data contracts and CI checks are the mature answer.

### 6.2 Role / scope questions

6. **"What does the first 90 days look like for the person who gets this role?"**
   → Signals you think in milestones and deliverables.

7. **"What's the biggest ambiguity the team is dealing with right now?"**
   → Tests whether the team is OK with messy problems (you want yes).

8. **"What's the gap between the team's current scope and where you want it to be in a year?"**
   → Tells you what you'd actually own if you joined.

### 6.3 Meta-specific questions

9. **"How does this team use Meta's internal tools (ODS, Dataswarm, ETLs) versus building its own?"**
   → For a DE role, this is essential — you don't want to spend your first quarter re-inventing what ODS already gives you.

10. **"How does the team balance Move Fast with the size of changes that ship to [surface]?"**
    → Tests whether the team actually does Move Fast or has calcified into process.

### 6.4 Questions to AVOID asking

- ❌ "What's the work-life balance?" (HR concerns, not interviewer)
- ❌ "What's the comp?" (not this round)
- ❌ "How do I get promoted?" (premature)
- ❌ "What's Meta's stock going to do?" (not their call)
- ❌ Yes/no questions that don't open a conversation

---

## 7. Red Flags to Avoid

Common mistakes that drop candidates from L6 → L5 → L4 in Round 5.

### 7.1 Story red flags

| Red flag | Why it's bad | What to do instead |
|----------|--------------|--------------------|
| **"We" every sentence** | No specific ownership visible | Force yourself to say "I decided" / "I owned" at least 3x per story |
| **No numbers** | Sounds like L4 contribution | Memorize 3 metrics per story: time, cost, quality |
| **Skipped to the result** | Hides the hard part | Describe the moment of decision explicitly |
| **Blamed others** | Anti-Meta (Be Open) | "The system failed, not any individual — here's what I changed" |
| **No tradeoffs** | No decision-making visible | Always say "I chose X over Y because Z" |
| **No prevention** | One-time hero, not durable | Always say "I built X so this couldn't happen again" |
| **"It worked out"** | Lucky, not skilled | "I chose the high-probability path because [reason]" |
| **Stale story (3+ years)** | Signals no recent L6 work | Prep at least 1 story from the last 12 months |

### 7.2 Delivery red flags

| Red flag | Why it's bad |
|----------|--------------|
| Rambling past 2 minutes on context | They're timing you; cut to the action |
| Defensive about failure | Meta values learning from failure, not perfection |
| Badmouthing ex-manager/colleagues | Direct fail — kills Be Open signal |
| Vague role ("I led the team") | They want to know what YOU did, not your title |
| No follow-up on the metric ("it improved") | "Improved from X to Y over Z weeks" |

### 7.3 The killer red flag: no system left behind

If you describe a great action with great metrics, but **never mention what you left behind**, the interviewer thinks:
- "Will this person do this once and move on, or build durable systems?"

Always end with: **"I built X (runbook, dashboard, SLO, contract, test, alert), and it's now used by N people / N teams / became the team standard."**

---

## 8. Mock Question Practice List (20 questions)

Rehearse these out loud. Time yourself. Cut anything over 4 minutes.

### 8.1 Core ownership questions (must nail)

1. **"Tell me about a project you owned end-to-end."**
   - *Tests:* All 6 ownership layers
   - *Prep:* Pick your strongest project. Lead with the metric. End with the system.

2. **"Describe a time you took on something beyond your defined scope."**
   - *Tests:* Beyond-scope layer
   - *Prep:* A story where you saw a gap no one owned and you picked it up. Quantify what would have happened if you hadn't.

3. **"Tell me about a time you disagreed with your manager."**
   - *Tests:* Tough calls + Be Open
   - *Prep:* Pick a story where you pushed back with data, escalated respectfully, and either got your way OR accepted the call and shipped.

4. **"When did you decide to escalate vs. handle something yourself?"**
   - *Tests:* Judgment, calibration
   - *Prep:* Two stories — one where you escalated correctly, one where you handled it yourself. Show you have a framework (e.g., "I escalate when it's blocking >N hours OR >$X impact").

5. **"Tell me about a time you had to make a decision with incomplete information."**
   - *Tests:* Move Fast + ownership
   - *Prep:* Show you defined the unknowns, ran the smallest experiment, and committed. Don't pretend you had no risk.

### 8.2 Operational / data questions (role-specific)

6. **"Tell me about a production incident you owned."**
   - *Tests:* Durability, on-call readiness
   - *Prep:* Use the L6 incident template from §4.3.

7. **"Describe a data pipeline you built end-to-end. What did you leave behind?"**
   - *Tests:* End-to-end + durability for DE
   - *Prep:* Include the runbook, the dashboard, the SLA. End with "still in prod, N teams depend on it."

8. **"Tell me about a time you improved a system's reliability."**
   - *Tests:* Durability + technical depth
   - *Prep:* p95, MTTR, SLO, recurrence prevention.

10. **"Have you ever had to push back on a technical decision? What did you do?"**
    - *Tests:* Code wins arguments + Be Open
    - *Prep:* Show you prototyped or ran a benchmark, not just argued.

11. **"Tell me about a time you defined a metric that didn't exist."**
    - *Tests:* Outcome focus, ownership of the problem
    - *Prep:* A story where you said "we can't optimize this without a metric" and built one.

### 8.3 Stakeholder / cross-functional questions

12. **"Tell me about a time you had to influence without authority."**
    - *Tests:* Leverage, cross-functional
    - *Prep:* A story where you didn't manage the people but had to convince them. Use data contracts, dashboards, or quick wins as your leverage.

13. **"Describe a conflict with a peer team. How was it resolved?"**
    - *Tests:* Conflict resolution, mature framing
    - *Prep:* The data contract story from the study guide works perfectly.

14. **"Tell me about the most cross-functional project you've shipped."**
    - *Tests:* Stakeholder mgmt
    - *Prep:* Name the teams, the cadence, how you kept them aligned.

### 8.4 Self-awareness questions

15. **"Tell me about a time you failed. What did you learn?"**
    - *Tests:* Self-awareness, learning
    - *Prep:* Real failure + specific system change. Don't fake humility.

16. **"What's the most ambiguous problem you've solved? How did you even know it was a problem?"**
    - *Tests:* Defining the problem
    - *Prep:* Lead with the signal that made you notice.

17. **"What would your last manager say is your biggest area for improvement?"**
    - *Tests:* Self-awareness
    - *Prep:* Real answer + what you've done about it.

### 8.5 Forward-looking questions

19. **"Tell me about the most technically ambitious project you've ever proposed."**
    - *Tests:* Be Bold
    - *Prep:* A moonshot story. Even if it didn't fully work, show the frame it did move.

20. **"What's something you want to learn or get better at?"**
    - *Tests:* Growth mindset
    - *Prep:* Be specific. "I want to learn to lead without authority at Meta's scale" beats "I want to be a better leader."

---

## 9. 48-Hour Prep Plan (Before the Mock)

### Day 1 — Story Mining (3 hours)

1. List **8 stories** from your last 3 years of work, across these buckets:
   - 2x incident/operational
   - 2x new system / greenfield
   - 2x conflict / cross-functional
   - 1x failure
   - 1x moonshot / beyond scope

2. For each, write the **one-line headline**: "[I did X], which [moved metric Y from A to B]."

3. Pick the **strongest 4**. These are your A-stories. The other 4 are backups.

### Day 1 Evening — STAR Drafts (2 hours)

4. For each A-story, write a 250-word STAR. Include:
   - 1 sentence context
   - 1 sentence "I owned X because Y"
   - 3-5 bullets of specific actions (with tool names, decision moments)
   - 1 sentence quantified result
   - 1 sentence "I left behind X (runbook/dashboard/SLO) which is now Y"

### Day 2 Morning — Rehearsal (2 hours)

5. **Time yourself out loud** for each A-story. Target: 3-4 minutes.
6. Practice the **opening sentence** of each story cold (the interviewer will interrupt if you ramble).
7. Practice the **closing sentence** with the system-prevention line.
8. Record yourself, listen back. Cut every "we" that should be "I".

### Day 2 Afternoon — Q Drill (1 hour)

9. Have a friend (or the notebook mock mode) hit you with the 20 questions.
10. For each, answer in STAR. After each, ask yourself: "Did I say I decided? Did I name a metric? Did I name what I left behind?"

### Day 2 Evening — Meta-Specific Polish (1 hour)

11. Read §1-§4 of this guide again.
12. Write out your **"tell me about yourself"** pitch cold. Target 90 seconds.
13. Write out your **3 questions for the interviewer**.
14. Read your A-stories one more time. Sleep.

### During the mock

- **First 30 seconds of each answer:** context + "I owned X because Y." Don't ramble.
- **3 minutes in:** you should be at the result.
- **Last 30 seconds:** the system you left behind.
- **If interrupted:** thank them, don't restart. Say "the punchline is [metric] and I left [system] behind."
- **If you blank:** "Let me think for 5 seconds" is fine. Then start with the context.

---

## 10. Cheat Sheet — Print This

```
L6 OWNERSHIP = I DECIDED + I DEFINED THE METRIC + I LEFT A SYSTEM BEHIND

EVERY ANSWER NEEDS:
  - Context (30s)         → Who, what, when, scale
  - "I owned X because Y" (10s)
  - Specific actions (2-3min) → tools, decisions, tradeoffs, "I chose A over B because C"
  - Metric (30s)          → moved X from A to B
  - System left behind (30s) → runbook, SLO, dashboard, contract, eval set
  - What I'd do differently (15s, optional)

"I" WORDS TO USE:    decided, owned, defined, chose, escalated, shipped, prevented
"WE" WORDS TO USE:   built, designed, debugged, paired, ran

L6 POWER PHRASES:
  1. "I owned it end-to-end, from problem definition to runbook."
  2. "I defined the metric because none existed."
  3. "I chose X over Y because [tradeoff in <10 words]."
  4. "I left a [runbook / dashboard / SLO / contract] that is now the team standard."
  5. "Zero recurrence in N months."

NEVER SAY:
  - "It was a team effort" (without naming your decision)
  - "I told my manager and they decided"
  - "We formed a committee"
  - "It improved" (no number)
  - "We did it" (no system left behind)
  - Anything bad about an ex-colleague

ALWAYS HAVE READY:
  - 4 A-stories (incident, new system, conflict, failure)
  - "Tell me about yourself" (90s, memorized)
  - 3 questions to ask
```

---

## 11. What to Do if You Don't Know an Answer

Honest framework — interviewers respect this more than bullshit:

1. **"Let me think for 5 seconds."** Pause. Then answer. Don't fill silence with garbage.
2. **If you don't have the story:** "I don't have a strong example for that. The closest I have is [X] — would that work?"
3. **If you genuinely don't know:** "I haven't faced that exact situation. My instinct would be [X] because [reason] — is that aligned with how you'd handle it?"
4. **If the question is unclear:** "Can I make sure I'm answering the right question? Are you asking [A] or [B]?"

These all show ownership of the conversation itself.

---

## 12. Post-Round: How to Debrief

After the mock, write down:

1. Which stories you used and how they landed
2. Where you rambled (cut next time)
3. Where you said "we" instead of "I"
4. Where you didn't quantify
5. Where you forgot the system-left-behind line
6. New questions you didn't expect

Then update your A-stories once and re-rehearse. Repeat until cold.

---

**You're ready when:**
- You can deliver any of the 4 A-stories in under 4 minutes, cold, no notes.
- Every story has a number, a decision, and a system left behind.
- Your "tell me about yourself" hits 90 seconds and ends with what you'll OWN at Meta.
- You have 3 sharp questions ready.

**Good luck. Own it.**