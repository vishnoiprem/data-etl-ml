# Demonstrate Behavioral Competencies (Ownership, Ambiguity, Collaboration, Prioritization)

## 1. Simple way to think
- The interviewer is building a competency map, not hearing a story. Each STAR should map cleanly to one competency: ownership ("I drove it"), ambiguity ("the goal was unclear, I defined it"), collaboration ("I brought teams together"), prioritization ("I said no to X to ship Y").
- Meta's DE bar values **scope of impact** (how many users/systems/teams) and **self-awareness** more than polish. Don't pick tiny stories.
- Prepare **6–8 stories** total and tag each with 1–2 competencies so you can flex based on follow-ups. One-size-fits-all answers feel rehearsed.
- Quantify both the problem (rows/sec, $ impact, users affected) and the outcome (latency cut, bug rate, adoption).
- Avoid "we" without "I." Interviewers are explicitly trained to detect credit-avoidance or credit-hogging. Be balanced.

## 2. Interview write-up (how to solve it)

**STAR — Ownership / Ambiguity hybrid:**
- **Situation:** Our growth marketing team was spending ~6 hours/week manually pulling campaign attribution from a fragmented stack: 3 ad platforms, a homegrown events pipeline, and a Looker dashboard that broke every time upstream schemas changed.
- **Task:** Leadership asked for "self-serve attribution." The requirements were vague — no SLA, no defined metric definitions, conflicting opinions on attribution model (last-click vs. data-driven).
- **Action:** I owned the project end-to-end. First, I ran a 2-week discovery: interviewed 8 stakeholders, wrote a one-pager defining 5 KPIs with SQL examples, and socialized it for sign-off (removed ambiguity). Then I built a dbt-modeled mart on top of our existing Airflow/Snowflake stack, added data tests (dbt tests caught a 4% revenue leak on day 2), and shipped a Mode dashboard with row-level filters. I partnered with the analytics eng team to deprecate the Looker model once adoption hit 80%.
- **Result:** Manual reporting time dropped from 6 hrs/week to 0. Adoption: 40+ weekly active users within 2 months. The revenue-leak bug alone recovered ~$180K/quarter in misattributed spend. Promotion committee cited this as a flagship project.

**What makes this answer strong:**
- Shows *both* ownership (drove end-to-end) and ambiguity handling (defined the metrics, got sign-off).
- Quantifies problem and outcome; the $180K is memorable.
- Names specific tools (dbt, Snowflake, Airflow, Mode) — proves it's a real DE story, not a PM story.
- Mentions collaboration (interviewed 8 stakeholders, partnered with analytics eng) without losing the "I drove it" spine.

## 3. Best optimized solution
Tighter version focuses the first sentence on impact, compresses the action into 3 verbs (define, build, partner), and ends with a reflective line: *"The lesson: when the spec is unclear, the highest-leverage move is to write the spec yourself, then socialize it."*

**What to prepare before the interview**
- A spreadsheet mapping 6–8 stories to competencies (ownership, ambiguity, collaboration, prioritization, conflict, failure).
- For each story: a one-line "headline," 3 quantification tags, and a one-sentence lesson learned.
- A "negative example" — a time things went sideways and what you learned. Meta almost always asks this.
- A clear 60-second, 3-minute, and 6-minute version of each story.

**Variations the interviewer might push on**
- *"What would you do differently?"* — Pick one real thing (e.g., "I should have looped in Finance in week 1, not week 4; cost us a re-do"). Never say "nothing."
- *"How did you handle pushback on the attribution model?"* — Use a small conflict story: who dissented, how you resolved with data, what you conceded.
- *"Tell me about a time you failed."* — Have a *genuine* failure ready. Frame as: what happened, your specific contribution to the failure, what you changed in your process.

**Red flags to avoid:** Vague "I helped the team..." openers; stories older than ~5 years; refusing to give specifics ("it was a complex situation"); claiming sole credit for team wins; no quantified outcome; no reflection/lesson. Interviewers will flag any story where you can't articulate what *you* did versus what the team did.