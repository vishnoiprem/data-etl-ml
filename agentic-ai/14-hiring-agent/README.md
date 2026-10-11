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
