# Project Impact, Mentorship, and Fair Credit Allocation

## 1. Simple way to think
- Meta's DE interview explicitly scores **multipliers**: a senior DE who makes 3 juniors better is worth more than one who ships 3x the code alone. This question is the multiplier test.
- The interviewer is watching for **two failure modes**: (a) the credit-hog who says "I" for everything, and (b) the credit-avoider who says "we" for everything. Both are red flags.
- Mentorship is broader than "1:1s with juniors." It includes code review quality, writing docs, designing systems that others can extend, and *naming* the people you learned from.
- Project-impact stories should answer: "If this project disappeared tomorrow, what would break, and for whom?"
- The "fair credit" prompt is often the differentiator between L5 and L6. Practice being specific about who did what.

## 2. Interview write-up (how to solve it)

**STAR — Mentorship + credit allocation:**
- **Situation:** I was the lead DE on a migration from a legacy Redshift-on-Postgres setup to a new Snowflake + dbt stack. I had 2 mid-level engineers (Priya, 2 yrs exp; Marco, 3 yrs exp) and 1 new grad (Aisha) reporting to me, and 4 analysts who depended on the old pipeline.
- **Task:** Ship the migration in 12 weeks with zero downtime, grow the team's dbt/Snowflake skills, and make sure analysts didn't lose trust.
- **Action:**
  - **Work division by interest + growth:** I gave Aisha the documentation & data-test suite (her stated interest, and the highest-leverage learning surface). Priya took the incremental-mart migration (her strength, with stretch goals on dbt macros). Marco led the cutover strategy and runbook (his growth area into senior).
  - **My role:** System design, the 3 hardest PRs, and code review. I instituted a "review rubric" doc so reviews taught, not just blocked — every comment had a "why" and a link to docs.
  - **Recognition:** In our team all-hands, I explicitly named each person in the demo and tied their work to the metrics. I made sure Priya's dbt macro got open-sourced internally under her name, and I nominated Aisha for our team's "rising engineer" award — she won.
  - **Credit honesty:** When the migration had a 4-hour partial outage in week 10, I told leadership the cause was a review I missed. I publicly named my miss in the postmortem and the change I made (added a staging-env load test to the runbook).
- **Result:** Migration shipped on time, 0 analyst complaints (down from baseline noise). Aisha was promoted to L3 within 9 months. Priya presented the dbt-macro work at our internal eng conference. The review-rubric doc was adopted by 3 other teams.

**What makes this answer strong:**
- Names each person, their level, and *why* you gave them that piece — shows intentional mentorship, not just delegation.
- Demonstrates "lift as you climb" — public recognition, awards, conference talk.
- Owns a public miss; fairness about failure is the strongest credit-allocation signal.
- Quantified the impact (zero downtime, 0 analyst complaints) and the *people* outcomes (promotion, conference talk).

## 3. Best optimized solution
The polished version compresses the action into a single arc: *"I divided work by interest and growth, held the riskiest pieces myself, made review a teaching tool, and gave public credit — including public ownership of a miss."* Reflection: *"A team's output is bounded by its weakest reviewer; mentorship is the highest-leverage infrastructure work a senior DE can do."*

**What to prepare before the interview**
- A specific mentee story with a *before/after* skill delta (not just "I mentored them").
- An example where you gave visible credit that you could have taken — concrete, recent.
- A time you received mentorship and what you changed because of it (signals you can be mentored).
- A public miss you owned. Have the postmortem link or the exact words handy.

**Variations the interviewer might push on**
- *"How do you give feedback a junior doesn't want to hear?"* — Use a specific story with a technique (e.g., "feedback sandwich is dead — I describe the behavior, the impact, the question of what got in the way").
- *"Tell me about a mentee who didn't work out."* — Be honest and kind. Don't blame them. Explain what you learned about *your* matching/hiring signal.
- *"How do you decide who gets the visible work?"* — Show a principle: rotation, growth area, who needs the visibility for promo/comp. Avoid "I take the hard stuff because I'm best at it" — that's a credit-hog tell.

**Red flags to avoid:** Generic "I love mentoring" without a story; mentee names that are clearly inflated; claiming credit for outcomes you didn't influence; refusing to name a miss; "I delegated" with no detail on *how* you set them up for success; treating mentorship as a side hobby rather than a primary job.