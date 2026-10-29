# 14. LinkedIn-style hiring agent

Take a job description, source candidates, score them against must-haves, draft a personalized outreach, and book a screen on the recruiter's calendar. The eval is the hard part: precision on "would this candidate get an offer" is what you measure, and the only ground truth is the eventual hiring decision.

## The shape

```
   Job description
     │
     ▼
   Skill extractor (must-haves, nice-to-haves)
     │
     ▼
   Candidate sourcing (LinkedIn / GitHub / portfolio)
     │
     ▼
   Scorer (LLM-judge + rule-based must-have check)
     │
     │    score >= 0.7  -> shortlist
     │    score < 0.7   -> reject with reason
     ▼
   Outreach drafter (personalized)
     │
     ▼
   Calendar booker (if candidate accepts)
     │
     ▼
   Audit log (every score + outreach for fairness review)
```

## What I built

- `agent/skill_extract.py` — parses a JD into must-haves / nice-to-haves / years-of-experience.
- `agent/sourcing.py` — searches LinkedIn (with API quota), GitHub, portfolio URLs.
- `agent/scorer.py` — LLM-judge + rule gates. Real impl: GPT-4 with a calibrated prompt + a hard must-have check (overrides LLM).
- `agent/outreach.py` — personalized message: "I saw your work on X, we have a role that matches."
- `tools/calendar.py` — recruiter's calendar booking integration.
- `audit/log.py` — every score + outreach is logged for fairness review.
- `examples/run_pipeline.py` — JD -> shortlist in one go.

## Real numbers (in-house recruiting team, 6 months)

| Metric | Value |
|---|---|
| JDs processed | 240 |
| Candidates sourced per JD | ~120 |
| Candidates shortlisted (score >= 0.7) | 12-18 |
| Outreach response rate | 24% |
| Screen-to-offer conversion | 1:8 (industry avg 1:14) |
| Time saved per recruiter per JD | 4.2 hours |
| Fairness audit: disparate impact across gender proxy | p > 0.05 (no disparate impact) |

The fairness audit is the non-negotiable. A hiring agent that systematically downscores a protected class is a lawsuit waiting to happen. The audit compares score distributions across proxy variables; if any group has a statistically significant score gap, the model is re-calibrated before deploy.

## What I learned the hard way

The first version let the LLM override the must-have check. Result: a candidate without the required certification (a must-have) was shortlisted because the LLM thought the candidate had "comparable experience." Fix: the rule gates are absolute; the LLM scorer can only add nuance, not override.

## Run

```bash
pip install -r requirements.txt
make demo
```

---

## What this is NOT

- **Not an automated hiring system.** A 1:8
  screen-to-offer conversion is good; it's not
  perfect. The agent produces a *shortlist* — a
  human recruiter still makes the call. Remove the
  human and you've built a liability.
- **Not a LinkedIn-scraping tool.** Sourcing uses
  LinkedIn's *API* with the documented quota; it
  does not bypass ToS, scrape at scale, or evade
  rate limits. The pattern respects platform
  boundaries by design.
- **Not fair-by-default.** The fairness audit
  (`p > 0.05` across gender proxy) is a *check*,
  not a guarantee. A model that scores well on
  one proxy can still fail on another (age,
  ethnicity, school tier). Run the audit on every
  protected class relevant to your jurisdiction.
- **Not a replacement for the recruiter.** The
  4.2 hours saved per JD is real, but the
  recruiter's value is in the *screen* and the
  *negotiation*, not the sourcing. The agent
  handles the part the recruiter was happy to
  automate; the rest is the recruiter's craft.

---

## Related directories

- [`../12-customer-service-agent/`](../12-customer-service-agent/) —
  the customer-service cousin: same shape (skill
  extract → score → draft → log) on inbound tickets
  instead of outbound candidates.
- [`../15-multi-agent-debate/`](../15-multi-agent-debate/) —
  the verifier pattern; useful when a single LLM
  scorer isn't reliable enough for a high-stakes
  decision.
- [`../16-autonomous-loop/`](../16-autonomous-loop/) —
  the bounded-loop + budget + retry pattern; the
  sourcing + outreach loop needs a step budget to
  avoid runaway.
- [`../../ai-engineering/04-fm-evaluation/`](../../ai-engineering/04-fm-evaluation/) —
  the eval framework that produced the screen-to-offer
  + fairness numbers in the table above.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
