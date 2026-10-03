# Answer DE Behavioral and Ramp-Up Questions (Tight Deadlines, New Codebases, Ambiguity)

## 1. Simple way to think
- These questions test **learning velocity** and **execution discipline** under constraints — two things a new DE at Meta must demonstrate weekly.
- Ramp-up stories should reveal a *repeatable method* (not "I'm smart, I figured it out"). Interviewers want to know: do you have a system, or did you get lucky once?
- Tight-deadline stories are really **prioritization** stories. The interviewer is asking: can you cut scope intelligently without lying about scope?
- Ambiguity stories prove you can *create* clarity, not just survive it.
- For ramp-up questions specifically, the meta-skill is "learning out loud" — interviewers want to see how you'd onboard, not just that you can.

## 2. Interview write-up (how to solve it)

**STAR — Tight deadline + ramp-up:**
- **Situation:** I joined a new team that owned real-time user-activity ingestion (billions, customers/ingest-pipeline). I had 3 weeks before a board-level demo where I had to ship a new fraud-detection feature into the same pipeline.
- **Task:** I had to (a) understand a 4-year-old Scala/Akka codebase I'd never touched, (b) design a feature that wouldn't break the 99.95% latency SLO, (c) ship a tested PR before the demo.
- **Action:**
  1. **Ramp-up (week 1):** I didn't read code top-down. I traced 3 representative events end-to-end, drew the data-flow diagram myself, and wrote a 2-page "how this works" doc. I scheduled 30-min "office hours" with the 2 engineers who knew it best — gave them a list of 12 specific questions so I didn't waste their time. I read the last 50 PRs and the last 20 incident postmortems.
  2. **Prioritization:** I wrote down the 8 things the feature could be, then killed 6 with my tech lead in a 20-min meeting. Cut scope to: "score, log, alert" — no UI, no backfill, no dashboard.
  3. **Execution:** Pair-programmed the riskiest piece (the streaming join) with the senior engineer for 2 hours — caught a subtle watermark bug that would've shipped.
- **Result:** Shipped 4 days early. Zero production incidents in the first month. Board demo went well; the feature identified ~$1.2M/month of fraud. The ramp-up doc I wrote became the team's onboarding doc.

**What makes this answer strong:**
- Names a *repeatable* ramp-up method (trace events, draw diagram, interview experts, read postmortems) — not "I'm a fast learner."
- Demonstrates explicit prioritization (cut 6 of 8 features) — interviewers love scope-cutting.
- Shows judgment: pair-programmed the risky piece rather than guessing.
- Quantified outcome and turned a side effect (the doc) into durable value.

## 3. Best optimized solution
The polished version front-loads the *method*: *"My ramp-up playbook is: trace one transaction end-to-end, draw it, then ask experts the questions the diagram raises."* It ends with: *"The lesson: under a deadline, the highest-leverage work is deciding what not to build."*

**What to prepare before the interview**
- Your personal ramp-up *playbook* with 4–5 named steps. Be ready to defend each step.
- A tight-deadline story where you explicitly say what you didn't build (and why that was correct).
- A recent time you learned a new tool/framework fast — name what you read, who you asked, how long it took.
- An example of a feature/spec that arrived half-baked and how you added structure.

**Variations the interviewer might push on**
- *"What's the first thing you do on day 1?"* — Have a literal answer (e.g., "clone the repo, run the test suite, read the top-3 most-recently-merged PRs, schedule 1:1s"). Specificity signals seriousness.
- *"How do you know when to stop ramping up and start shipping?"* — Answer with a heuristic: e.g., "when I can predict where a change would land in the code, not just find it after the fact."
- *"Tell me about a deadline you missed."* — Be honest. The right answer admits miss, names the cause (over-scoping, unclear spec, blocked dependency), and explains the process change you made.

**Red flags to avoid:** Claiming you ramp up by "reading the docs" (no one does, and it signals you've never onboarded seriously); stories where the deadline was met but quality clearly suffered and you don't acknowledge it; "I just worked harder" as the strategy; refusing to name what you cut from scope.