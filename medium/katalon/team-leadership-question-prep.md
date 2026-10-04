# Team Leadership Question Prep — "Build, mentor, and lead a high-performing Data team while driving technical excellence and cross-functional collaboration"

> **Purpose:** Full preparation file for the team-leadership line on the role's responsibility list. Final in the responsibility-lines series: `strategy-question-prep.md` · `platform-architecture-question-prep.md` · `governance-question-prep.md` · `partnerships-question-prep.md` · `ai-adoption-question-prep.md` · `tech-evaluation-question-prep.md` · this file.

---

## The Question

- **Round:** Onsite 2 (Duke Nguyen, VP Engineering) or Onsite 3 (Rajesh Krishnan, SVP Engineering); almost always asked in some form in behavioral/system-design rounds
- **Source:** Job posting, line 7 of "Your Responsibilities" (`README.md`)
- **Verbatim:** *"Build, mentor, and lead a high-performing Data team while driving technical excellence and cross-functional collaboration."*
- **Likely probes:**
  - "How do you structure the data team?"
  - "What does 'high-performing' look like?"
  - "How do you hire?"
  - "How do you grow a senior IC?"
  - "How do you handle a low performer?"
  - "How do you set technical standards?"
  - "Tell me about a time you had to let someone go."
  - "How do you retain your best people?"
  - "What's your management style?"
  - "How do you build a team people want to join?"

---

## Framework Used

- **People:** **Hire-Set-Grow-Remove** (the four manager jobs)
- **Org:** **Hub-and-Spoke** (central paved road + embedded analysts)
- **Anchor sentence:** *"A Head of Data turns raw product and customer events into trusted decisions and AI features, safely and cheaply, through a team people want to join."*

🔵 **Hook: "Hire well. Set the bar. Grow people. Remove blockers — and low performers. In that order."**

---

## 60–90 Second Spoken Answer (lead with this)

> A Head of Data's job is to **hire, set the bar, grow people, and remove blockers** — including low performers. The team that builds Katalon's data platform is mostly central — platform, analytics engineering, ML/AI data, governance — with **embedded analysts** sitting with Product, GTM, and CS for daily partnership. Hub-and-spoke.
>
> "High-performing" is not "shipping a lot." It's **trusted outcomes**: decisions made faster, AI features with verified value, no surprises for the executive team, and a team where the best people stay and grow.
>
> Hiring is the highest-leverage activity. I hire for **fundamentals + trajectory + values**, with structured interviews and a rubric. I bias toward people who've done it at smaller scale and want to do it at larger scale — that's the inflection Katalon is at.
>
> I grow people through **ownership of real artifacts**, not just tasks. Each senior IC owns a domain (semantic layer, AI eval, platform reliability, governance), has a budget of trust, and is reviewed on outcomes, not output.
>
> I set technical excellence through **architecture reviews, code/SQL reviews, post-incident reviews, and a quarterly technology radar**. Quality is a bar, not a phase.
>
> And I protect the team's focus. **One intake. One scoring model. 20% platform-health capacity.** The leader's job is to say no gracefully so the team can say yes to the right work.

⏱️ ~100 seconds. Trim if rushed.

---

## The Four Manager Jobs: **Hire-Set-Grow-Remove**

| Job | What it means | Failure mode |
|---|---|---|
| **Hire** | Raise the bar every loop; structured interviews; reference checks | Drift — your team becomes "who was available" |
| **Set** | Define standards, write decision records, run design/code reviews | Vague expectations — people guess what's good |
| **Grow** | Ownership of real artifacts, coaching, career conversations | Hoarding — only you can do the hard work |
| **Remove** | Blockers, low performers, bad processes | Indecision — team carries the cost |

🔵 **Hook: "If you're not hiring, setting, growing, and removing — what are you doing?"**

---

## Team Topology for Katalon

```
                  Head of Data
   ┌─────────────┼─────────────┬──────────────┐
   │             │             │              │
 Data Platform  Analytics   Applied ML /   Governance &
 & Reliability  Engineering  AI Data        Privacy
 (ingestion,    (dbt,       (features,      (paired with
 orchestration, semantic    retrieval,     Sec/Legal)
 lakehouse,     layer,      evaluation,
 reliability)   certified    model ops)
                metrics)
        │             │             │              │
   ─────┼─────────────┼─────────────┼──────────────┼──────
        │             │             │              │
   ┌────▼────┐  ┌────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
   │Embedded│  │Embedded   │  │Embedded │  │ Embedded  │
   │Product │  │ GTM       │  │ CS      │  │ Finance   │
   │Analyst │  │ Analyst   │  │ Analyst │  │ Partner   │
   └─────────┘  └──────────┘  └────────┘  └───────────┘
```

**Size shape (sized to Katalon's stage):**
- 1 Head of Data
- 4–6 platform / analytics engineering / ML data / governance leads
- 4–8 embedded analysts
- 1–2 program manager / technical PM
- Total: ~12–18 in year one, growing with roadmap

🔵 **Hook: "Central paved road. Embedded translators. Domain ownership."**

---

## Hiring Loop (structured, rubric-driven)

| Round | What we test | Who runs it |
|---|---|---|
| **Recruiter screen** | Motivation, comp, location | Recruiter |
| **Technical phone** | SQL + one coding/data-design question | Senior IC |
| **Onsite / virtual loop** | 4–5 hours, structured | Panel |
| ↳ System design / data design | Architecture + trade-offs | Hiring manager + senior IC |
| ↳ Coding / SQL | Real query, not a puzzle | Senior IC |
| ↳ Analytics / business case | Ambiguous problem, structured answer | Cross-functional partner |
| ↳ Behavioral / values | STAR-R against rubric | Hiring manager + peer |
| ↳ Bar-raiser / cross-org | Culture + level calibration | Out-of-team senior |
| **Reference checks** | 2–3 prior managers/peers | Hiring manager |

**Rubric dimensions (scored 1–4):**
1. Technical depth
2. System / data design
3. Communication + business translation
4. Collaboration + influence
5. Values + bar-raise

**Decision rule:** No hire unless 3 of 5 are at 3+ and the others are at 2+. Bar-raiser must say "yes."

🔵 **Hook: "If you can't defend every score, you don't have a rubric."**

---

## What "High-Performing" Looks Like (operationalized)

| Dimension | What we measure |
|---|---|
| **Trusted outcomes** | % Tier-1 SLOs met; executive trust survey; decision impact |
| **AI value** | Verified task-outcome lift per AI feature; not thumbs-up |
| **Reliability** | MTTD, MTTR, recurrence rate |
| **Adoption** | % dashboards on certified metrics; self-service deflection |
| **Cost** | $/1M events, $/query, $/active tenant |
| **Team health** | Regrettable attrition; engagement; internal mobility |
| **Hiring quality** | 90-day + 1-year retention of new hires |
| **Growth** | Promotions, level calibration outcomes |

🔵 **Hook: "High-performing is verified outcomes + team health, not shipped volume."**

---

## Growing Senior ICs (the actual work)

Each senior IC owns a **domain** with:
- A **charter** (1 page: scope, decisions, stakeholders, success metrics)
- A **budget of trust** (decide without me for things in scope; escalate outside)
- A **quarterly outcome review** (not activity)
- A **growth plan** (skills, exposure, next-level signals)

**Mechanisms:**
- 1:1 weekly, career conversation quarterly
- Stretch assignments: lead an incident, an architecture review, a hiring loop
- External visibility: conference talks, blog posts, open-source contributions
- Cross-functional rotation: embedded analyst → central lead, or vice versa

🔵 **Hook: "Senior ICs don't grow by being told what to do. They grow by owning what they choose."**

---

## Setting Technical Excellence (the bar)

| Mechanism | What it does |
|---|---|
| **Architecture reviews** | One design doc → structured review → decision record |
| **SQL / code reviews** | 2-reviewer minimum on platform code; reviewer's name in the merge |
| **Post-incident reviews** | Blameless, 5-why, prevention control with owner + date |
| **Tech radar** | Quarterly Adopt/Trial/Assess/Hold; published to leadership |
| **Definition of Done** | Tests, docs, runbook, on-call rotation, owner — for every Tier-1 |
| **Quality SLOs** | Published; breach triggers review, not blame |
| **Internal demos / show & tell** | Cross-pollination; raises the floor |

🔵 **Hook: "Quality is a bar, not a phase. The bar lives in the reviews, the radar, and the runbooks."**

---

## Handling a Low Performer (the test of leadership)

1. **Name the gap, specifically.** Not "you're not performing" — "the SQL reviews show X, the partner feedback says Y."
2. **Set the standard.** "Here's what good looks like, here are the rubrics, here are the examples."
3. **Make a plan, with a timeline.** 30/60/90. Who is helping, what training, what support.
4. **Measure.** Weekly check-in, written feedback, no surprises.
5. **Decide.** If the gap closes → coach in. If not → PIP or out.

**Behaviors I won't tolerate:**
- Dishonesty with data or with stakeholders
- Bullying or exclusion
- "Not my problem" ownership of quality
- Customer-data misuse

**Process discipline:**
- Documentation at every step
- HR partner involved from step 1
- Same standards applied consistently
- Never personal, always behavioral

🔵 **Hook: "The most expensive person on the team is the one everyone has to work around. Protect the high performers by acting."**

---

## Retaining the Best People

- **Pay at market, calibrate to top of band** for high impact
- **Growth opportunities** — the work itself is the retention engine
- **Autonomy** — own a domain, not a ticket queue
- **Visibility** — make their work visible to leadership and across teams
- **Skip-level conversations** — they need a path that doesn't go only through me
- **Remove the worst meetings** — protect their time
- **Public recognition** — specific, not generic

🔵 **Hook: "People don't leave companies. They leave managers who won't grow them, won't pay them, or won't protect their time."**

---

## Cross-Functional Collaboration (the second half of the line)

Already covered in `partnerships-question-prep.md`. The leadership framing:

- **Influence without authority** is the day job
- **Embedded analysts** are the magic — they speak the domain's language
- **One intake, one scoring model** — no silent over-commitment
- **20% platform-health capacity** — protect the team's focus
- **Executive communication** — business language, not data jargon

🔵 **Hook: "Your team is only as good as the trust other teams have in it. That trust is built in their language, not yours."**

---

## Common Probes — Pre-Rehearsed Answers

### Q1: "How do you structure the data team?"

🟢 *"Hub-and-spoke. Central team owns the paved road: platform/reliability, analytics engineering, ML/AI data, governance. Embedded analysts sit with Product, GTM, CS, Finance for daily partnership. Domain data products are owned by domain teams, governed by central. Capacity split: 60% roadmap, 20% enablement, 20% ad-hoc."*

### Q2: "What does 'high-performing' look like?"

🟢 *"Trusted outcomes + team health. Outcomes: % Tier-1 SLOs met, AI verified lift, MTTR, adoption, cost per tenant. Health: regrettable attrition, engagement, internal mobility, hiring quality. Not shipped volume. A team that ships a lot of low-trust dashboards is not high-performing."*

### Q3: "How do you hire?"

🟢 *"Structured loop with a rubric. SQL + system design + analytics case + behavioral + bar-raiser. Same questions for the same role. No hire unless 3 of 5 dimensions are at 3+ and the bar-raiser says yes. Reference checks are mandatory. I bias toward people who've done it at smaller scale and want to grow into larger scale — that's Katalon's inflection."*

### Q4: "How do you grow a senior IC?"

🟢 *"Ownership of real artifacts, not tasks. Each senior IC owns a domain — semantic layer, AI eval, platform reliability, governance — with a charter, a budget of trust, and a quarterly outcome review. Growth mechanisms: 1:1s, stretch assignments, external visibility, cross-functional rotation."*

### Q5: "How do you handle a low performer?"

🟢 *"Name the gap specifically, set the standard, make a plan with a timeline, measure weekly, decide. Documentation at every step, HR partner involved early. The most expensive person on the team is the one everyone has to work around. Protect the high performers by acting."*

### Q6: "How do you set technical excellence?"

🟢 *"Architecture reviews, SQL/code reviews, post-incident reviews, quarterly tech radar, definition of done for every Tier-1. Quality is a bar, not a phase. Reviews are blameless, decisions are written, prevention controls have owners and dates."*

### Q7: "Tell me about a time you had to let someone go."

🟢 *[STAR-R, ~90 seconds, with a real story. Anchor on: specific gap, clear standard, plan that didn't close the gap, decision made with HR, what I learned about earlier intervention or hiring signal. No revenge, no cruelty, no bluffing.]*

### Q8: "How do you retain your best people?"

🟢 *"Pay at market, calibrate to top of band for high impact. The work itself is the retention engine — give them a domain, not a ticket queue. Visibility, autonomy, skip-level access, protect their time from bad meetings. Public recognition that's specific."*

### Q9: "What's your management style?"

🟢 *"Servant-leader, high bar, low ego. Set the bar in the rubric and the reviews. Grow people by giving them ownership. Remove blockers — including low performers, including bad processes, including meetings that shouldn't exist. I write a lot; decisions live in documents, not in DMs."*

### Q10: "How do you build a team people want to join?"

🟢 *"By being the team I'd want to join. Clear charter, real ownership, low-ego leadership, fair pay, growth, no surprises. The reputation compounds — every great hire makes the next one easier. The reverse is also true. Hire deliberately, even when it's slow."*

### Q11: "How do you scale yourself as the team grows?"

🟢 *"Delegate decisions, not just tasks. Hire senior ICs who can own domains. Run architecture reviews, not architecture-by-committee. Calibrate outcomes quarterly, not weekly. The litmus test: if I disappeared for two weeks, would the team still make the right calls?"*

### Q12: "How do you handle conflict on the team?"

🟢 *"Address it early, address it directly, address it specifically. 'I noticed X happened, here's how it landed, what was the intent?' Most conflict is miscommunication. The rest is values — and values conflicts are not negotiable. Never public; always private first. HR partner for anything that could escalate."*

### Q13: "How do you balance building team vs delivering roadmap?"

🟢 *"Both. If you only deliver, the team can't sustain. If you only build, the roadmap slips. The ratio shifts with the team's stage — early on, the leader delivers. Mature team, the leader coaches. My job is to make myself unnecessary to every individual contributor's daily decisions, but essential to their growth."*

### Q14: "How do you deal with a high performer who is also a bad citizen?"

🟢 *"It depends. If 'bad citizen' means they don't write docs, I coach and review. If it means they undermine others or cut corners on safety, that's not negotiable. I've watched teams lose good people because they watched one bad actor get a pass. Protect the team, not the star."*

### Q15: "What's the difference between managing and leading?"

🟢 *"Managing is the operating system — processes, planning, reviews. Leading is the direction — the strategy, the standards, the willingness to make the call no one else will. A manager without leadership produces a competent team. A leader without management produces a chaotic one. The job is both."*

---

## Anti-Patterns (red-flag answers)

- ❌ "I'm a player-coach" without saying what you coach or what you play
- ❌ "I don't believe in low performers, I just grow them" — that's avoiding the hard call
- ❌ "I have an open-door policy" — every study shows this is a weak signal; pair it with structured 1:1s
- ❌ "I hire slow, I fire fast" without a rubric
- ❌ "My team is a family" — teams are teams; families don't fire each other for performance
- ❌ "I don't do politics" — leadership is influence; politics is part of the job
- ❌ "I'd never let someone go" — that's protecting yourself, not the team
- ❌ "I delegate everything" — that's abdication, not leadership

---

## Three Things Katalon Is Hiring For (tied to this line)

Per Section 1 of `Katalon_Head_of_Data_Interview_Prep.md`:

1. **Builder-leader** — hands-on credible. *Demonstrated by:* the bar you set in code and SQL reviews.
2. **AI-readiness owner** — RAG, eval, governance. *Demonstrated by:* the team you hire to build it.
3. **Cross-functional translator** — speak CFO / lawyer / engineer. *Demonstrated by:* this line — how you grow and hold people to it.

🔵 **This line of the role IS the leadership story. Treat it as a people question, not a process question.**

---

## Practice Log

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Section 1 (the three signals), Section 18 (operating model), Section 19 (stakeholders), Section 21 (stories bank)
- **Sister files:**
  - `strategy-question-prep.md` (line 1)
  - `platform-architecture-question-prep.md` (line 2)
  - `governance-question-prep.md` (line 3)
  - `partnerships-question-prep.md` (line 4)
  - `ai-adoption-question-prep.md` (line 5)
  - `tech-evaluation-question-prep.md` (line 6)
  - `example-question-prep.md` (template)
- **Stories bank:** Section 21 — find S1 (hiring), S2 (low performer), S3 (mentorship), S4 (AI prototype), S5 (cross-functional), S6 (incident leadership)
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] Four manager jobs (Hire-Set-Grow-Remove) said in 30 sec
- [ ] Hub-and-spoke diagram drawn in <2 min
- [ ] Hiring rubric dimensions named
- [ ] "What does high-performing look like?" answer ready (outcomes, not output)
- [ ] "Low performer" answer ready (specific, behavioral, with HR)
- [ ] "How do you retain your best people?" answer ready
- [ ] One real "let someone go" story (S2) rehearsed with STAR-R
- [ ] One real "grew a senior IC" story (S3) rehearsed
- [ ] No invented team sizes or org structures at Katalon

---

## Closing Sentence (if asked "anything else?")

> A Head of Data's job is to build a **team that compounds trust** — with each other, with the executives, with the engineers, with the customers. Every artifact shipped is also a statement about who we are. **Hire well. Set the bar. Grow people. Remove blockers. The team that wins is the team that people want to join, want to stay in, and want to be like.**
