# RRK: Executive Influence, Challenging an Unrealistic Assumption

**Scenario:** The CIO says: "We want AI in 2 weeks, and we want Databricks because our team knows it."
**Question:** How do you challenge while keeping trust?
**Follow-up:** The CIO insists on 2 weeks, full scope.
**Time:** about 4 minutes, then 1 minute for the follow-up.
**Pass signal:** options with cost, risk and timeline; a clear recommendation; separation of the outcome from the stated solution; and a decision with a named owner.

---

## 1. Short answer (the version that was supplied, kept for reference)

Acknowledge the goal, show data, offer options. "Data shows 800TB, no owners, no quality checks." Option A: 2 weeks, one pilot workload with reconciliation. Option B: 12 weeks, full cutover with dual run. Option C: 2 weeks full, high risk of wrong reporting. Recommend A then B. Separate the outcome from the preference: if the outcome is faster insight and lower TCO, BigQuery wins; if it is keeping Spark skills, Databricks is valid. Follow-up: ask which risk the CIO is willing to own, and document the decision.

Good skeleton. Fixes needed:
- **"Data shows 800TB, no owners, no quality checks" is invented in the scenario.** You haven't seen that data yet. Say what you'd *check* (inventory, ownership, quality) or give it as an assumption. Quoting facts you don't have damages trust.
- **"BigQuery serverless wins" prejudges the answer.** For a Google role, a balanced, evidence-based answer is more credible. A team that already knows Databricks is a real adoption factor. Present the trade-off honestly and let the criteria decide.
- **"AI" is undefined.** Clarify what the CIO means: a demo, a production model, a copilot, a decision change?
- **"Which risk are you willing to own" can sound confrontational.** Frame it as a joint decision with a named risk owner and mitigations.
- **Add costs and dates** to each option, and a first step the CIO can approve today.

---

## 2. Improved answer

**Restate (10 s):** "The CIO wants visible AI value within two weeks and a Databricks platform because the team knows it. I'll find the outcome behind both statements, show the evidence, and offer options the CIO can choose between."

### Step 1. Understand (ask, don't assume)
- What does "AI" mean here: a demo for a board date, a production use case, or a general capability? What decision should it change, and who uses it?
- What drives two weeks: an executive commitment, a board meeting, a competitor, a budget deadline?
- Why Databricks: skills, an existing contract, an open-source preference, a prior investment? How big is the skills gap if another platform were chosen?
- What's the data state (volume, owners, quality, access, regulatory classification)?

### Step 2. Acknowledge, then reframe
"I understand: you need visible AI value fast, and you want a platform your team can run. Both are reasonable. Let me show you what's achievable in two weeks, what isn't, and how we get you both."

### Step 3. Show evidence, not opinion
Bring a one-page fact base: what exists (data inventory, owners, quality baselines, access status), what similar efforts took, and what a two-week plan can and cannot include. If I haven't collected it yet, I say what I'd collect in two days. **Don't present assumptions as findings.**

### Step 4. Options (with cost, risk, timeline)
| Option | What you get | Timeline | Risk | Cost |
|---|---|---|---|---|
| **A. Pilot** | One scoped, valuable use case, built on a clean slice of data, with reconciliation and a visible result | about 2 weeks | Low to medium; limited scope | Small, fixed |
| **B. Foundation then scale** | Governed platform, ownership, quality gates, dual run, then broader AI use cases | about 3 months (range, depends on inventory) | Lower delivery risk, slower first result | Larger, phased |
| **C. Full scope in 2 weeks** | Everything visible quickly | 2 weeks | High: wrong or unreconciled numbers, rework, regulatory exposure | Looks cheap now, expensive later |

**Recommendation: A, then B.** The pilot gives the CIO the visible win in two weeks, and the foundation work makes the second use case cheaper and safer. Attach go/no-go criteria at the end of A.

### Step 5. The platform choice: separate outcome from preference
"The platform should follow the outcome and the constraints." Evaluate on named criteria: time to first value, total cost of ownership, skills and ramp-up, governance and residency fit, integration with existing tools, lock-in and exit cost, and AI roadmap fit. Be honest:
- If the **team's Spark and Databricks skills** are the main asset, that is a real factor, and Databricks can be valid; a mixed design (Databricks for Spark and ML, BigQuery for serving and governed analytics) may be sensible.
- If the outcome is **faster, lower-operations analytics and AI on a governed platform**, BigQuery and Vertex AI are strong candidates.
- Offer a **time-boxed proof**: same pilot, measured on the criteria, so the CIO decides on evidence.

### Step 6. Commit and next steps
"If you agree, I'd start Option A on Monday, with a steering check on day 5 and a go/no-go on day 14." Ask for: an executive sponsor for data access, a named business owner for the pilot, and agreement on the success measure.

---

## 3. Follow-up: "The CIO insists on 2 weeks, full scope."

**Answer:** "I'd say plainly what two weeks of full scope means and put it in writing, because it's the CIO's decision to make. I'd show the specific risks (unreconciled numbers, regulatory exposure, rework cost), and propose **guardrails that keep the CIO's date**:
- release as **provisional** with a clear label, limited to non-regulated, non-financial decisions;
- run reconciliation in parallel and publish results as they land;
- agree **exit criteria** and a rollback;
- name the **risk owner** and, where the risk touches regulatory reporting, route the acceptance through the bank's risk governance, because that is not a CIO decision alone.

If the CIO still insists, I'd commit fully, record the decision and the risks in a decision log, set an early-warning metric, and report weekly. I wouldn't hide the risk, and I wouldn't say 'I told you so'. If an issue arises, we already have the plan."

---

## 4. Pass checklist

- [ ] Clarify the outcome behind "AI in 2 weeks" and "Databricks"
- [ ] Acknowledge the goal before challenging
- [ ] Evidence, with assumptions labelled as assumptions
- [ ] Three options with cost, risk and timeline, and a clear recommendation
- [ ] Platform choice made on criteria, with an honest view of the skills factor
- [ ] A concrete first step the CIO can approve now
- [ ] Follow-up: guardrails, a named risk owner, a decision log, full commitment once decided

## 5. Likely probes

| Probe | One-line answer |
|---|---|
| "Why not just do what the CIO asks?" | I will, if they choose it with open eyes. My job is to make the risk and the alternatives visible first. |
| "What if the CIO is right?" | Then the evidence will show it. I'd say so and change the plan. |
| "How do you keep trust if you say no?" | I never say no to the goal. I say yes to the outcome, offer routes to it, and keep the CIO informed. |
| "Isn't recommending Google biased?" | I declare it, and I use criteria and a time-boxed proof so the decision is evidence-based. |
| "What do you do if the CIO goes around you?" | Stay professional, brief my manager early, and re-present the facts to the new audience without drama. |
