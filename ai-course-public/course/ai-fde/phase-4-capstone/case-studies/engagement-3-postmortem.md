# Case Study 3 — Postmortem: the Week-11 Hallucination Incident (2026-W11)

> **TL;DR.** On a Wednesday at 14:23 SGT, the PacificFreight drafter emitted **4 hallucinated drafts in 12 minutes**, misreporting shipment locations (saying "in HCMC" when they were still in Singapore). Mei reverted all 4 within 2 minutes each. I rolled back the deploy at 14:45. Total recovery time: **38 minutes** (vs 60-min SLO). Root cause: a 12-character prompt copy-edit ("HCMC" → "Ho Chi Minh City") that bypassed the circuit breaker during the deploy window and was combined with an unreported customs-system outage that left 4 shipments with unclear destinations. **The fix:** move the eval set into CI as a PR gate (fail on any metric drop > 0.05); add a post-deploy breaker-exercised hook; ban deploys during Mei's peak hours (14:00-16:00 SGT). **The lesson:** incidents are inevitable; the eval-set-in-CI is the cheap prevention; the runbook is the cheap recovery. **Mean Time To Detect (MTTD): 2 min** (Mei's re-read). **Mean Time To Recovery (MTTR): 38 min** (Daniel's rollback). **Customer impact: 4 drafts, all reverted before send.**

---

## 1. Severity classification (the taxonomy we use)

| Severity | Definition | Customer impact | Response time | Page |
|---|---|---|---|---|
| **SEV-1** | All users, all drafts, > 30 min | Service unusable | < 60 min | Daniel + FDE |
| **SEV-2** | One user, all drafts | Mei blocked | < 4 hr | Daniel |
| **SEV-3** | Few drafts, breaker caught | Sub-perceptible | < 24 hr | Daniel (async) |
| **SEV-4** | No user impact, internal-only | None | Next iteration review | Log only |

This incident is **SEV-1 candidate, downgraded to SEV-2** because: (a) Mei reverted all 4 drafts before sending, so customer-facing impact was zero; (b) only 4 of ~20 concurrent drafts were affected (the 4 shipments with unclear destinations due to the customs outage). The taxonomy lets us treat the same technical failure as different severities based on blast radius, not blast magnitude.

### 1.1 Blast-radius × blast-magnitude matrix

|       | ≤ 5% users | ≤ 25% users | ≤ 100% users |
|---|---|---|---|
| **No customer-visible error** | SEV-4 | SEV-3 | SEV-3 |
| **Customer-visible error (reverted)** | SEV-2 (this incident) | SEV-1 | SEV-1 |
| **Customer-visible error (sent)** | SEV-1 | SEV-1 | SEV-1 |

---

## 2. Timeline (blameless, all times SGT, UTC+8)

| Time | Event | Actor | Evidence |
|---|---|---|---|
| **09:00** | Normal iteration cadence: eval set ran, faithfulness 0.94, ansrel 0.91, no regression | Daniel | `eval_report_week11.md` |
| **14:14** | Customs-system outage begins upstream (4 shipments lose destination signal) | Customs (3rd party) | Customs vendor postmortem (not public) |
| **14:20** | FDE merges PR #247: prompt string "HCMC" → "Ho Chi Minh City" | FDE | `git log`, PR #247 |
| **14:21** | CI runs unit tests; PR merges | FDE | `actions/run/1234567` |
| **14:23** | Deploy to uvicorn VM; rollout completes | Daniel (cron) | `journalctl` |
| **14:23** | Mei sends email about PF-1002; drafter drafts "delivered in Ho Chi Minh City" | Mei + drafter | `usage.jsonl` row 4287 |
| **14:23** | Mei re-reads draft, notices PF-1002 is still in Singapore, reverts | Mei | Slack DM to Daniel |
| **14:25** | Daniel opens eval set, runs against current deploy | Daniel | terminal log |
| **14:25** | **Eval green (0.94, no regression)** — Daniel does not rollback | Daniel | reasoning below |
| **14:31** | Daniel reproduces deploy to previous commit (09:00); eval back to 0.94 | Daniel | `git checkout` + redeploy |
| **14:33** | Mei reports 3 more hallucinations: PF-1004, PF-1006, PF-1008 | Mei | Slack DM |
| **14:38** | FDE paged; reviews `git diff main..HEAD` | FDE | PagerDuty |
| **14:45** | Root cause identified: prompt change + customs outage unreported | FDE | reasoning below |
| **14:53** | Hotfix: revert prompt, re-run eval, redeploy | Daniel | terminal log |
| **15:01** | Eval green; Mei confirms no more hallucinations | Mei | confirmation |
| **15:01** | **Customer-facing impact: 4 drafts, all reverted, $0 of customer trust lost (per Mei's report)** | — | Slack |

**Total incident duration: 38 minutes** (14:23 first hallucination → 15:01 all-clear). **MTTD: 2 minutes** (Mei's re-read caught the first hallucination). **MTTR: 38 minutes.** Within the 60-min SEV-1 SLO.

---

## 3. Root cause (5 Whys — the deepest layer)

### 3.1 The proximate cause

A 12-character prompt change ("HCMC" → "Ho Chi Minh City") deployed at 14:23. The new prompt was not seen by the eval set before deploying. The eval set has 30 rows with the standard fixtures; the deploy window happened during an unrelated customs outage.

### 3.2 The 5 Whys

| # | Question | Answer |
|---|---|---|
| 1 | Why did 4 hallucinated drafts get sent? | Mei noticed but the 30-min deploy had already generated 12 drafts and 4 of them got the destination wrong. |
| 2 | Why did the destination entity-linking fail? | The LLM started treating "Singapore" as a fallback destination when it couldn't determine the actual destination from the context. The context was empty because the customs system was down. |
| 3 | Why was the context empty? | The retrieval layer reads `shipments.json`, which is updated by a cron from the customs API. The customs API was down; the cron had failed for 6 hours; no one noticed. |
| 4 | Why did no one notice the cron had failed? | The cron failure didn't trigger an alert because we don't have an alert on cron-failure for non-revenue-critical jobs. The eval set doesn't exercise the "shipment data is empty" case. |
| 5 | Why didn't the eval set catch the prompt regression? | Because the eval set doesn't include the prompt-change-fixture — the 30 rows are stable, the prompts change. The deploy pipeline runs unit tests only, not the eval set. |

**The deepest root cause: the eval set was not in the CI pipeline.** Everything above (LLM behavior, retrieval behavior, cron failure) was incidental; the CI gap was the structural failure.

### 3.3 The causal chain diagram

```
  Customs API down ─────────► Retrieval returns empty
       │                          │
       │                          ▼
       │                    LLM context is empty
       │                          │
       │                          ▼
       │                    LLM falls back to "Singapore" as
       │                    a default destination
       │                          │
       │                          ▼
       │                    4 hallucinated drafts
       │                          │
       │                          ▼
       │                    Mei re-reads + reverts (MTTD 2 min)
       │                          │
       │                          ▼
       │  PR #247 deploys ─► Slower recovery (deploy
       │  during peak         window overlaps with the
       │                      incident)
       │
       ▼
  Eval set NOT in CI ───► PR #247 merged without
                            eval-gate check
```

The eval-set-in-CI gap is the structural fix; the other 3 are tactical fixes that reduce blast radius but do not prevent the regression class.

---

## 4. What went well (the 3 wins)

| Win | Why it mattered | Quantified |
|---|---|---|
| **Mei re-reads every draft before sending** | Caught all 4 hallucinations before customer impact | MTTD = 2 min vs typical AI-deployment MTTD of hours-to-days |
| **Daniel had the eval set ready to run in 5 min** | Made rollback a deterministic decision, not a guess | 5 min from "Mei reports" to "deploy reverted" |
| **The runbook section "hallucination detected" was up to date** | Daniel executed the playbook without paging me for the first 22 minutes | 22 min solo recovery before FDE page |

### 4.1 Why Mei's re-read is the unsung hero

Mei's habit of re-reading every draft before sending is **the single most important defense in this system**. The eval set catches regressions in batch (weekly); the circuit breaker catches live failures; the re-read catches anything the eval set didn't anticipate. A P95 cost of 0.3s per draft × 150 drafts/day = 45 seconds/day of Mei's time. Worth it. **The most important PE habit in the entire engagement is making sure the user re-reads LLM output before sending.** I documented this in the runbook's "Operational Boundaries" section.

---

## 5. What went poorly (the 3 losses)

| Loss | Why it happened | Blast radius |
|---|---|---|
| **Eval set was NOT in the CI pipeline** | PR #247 merged without eval-gate; the deploy was "tested but not evaluated" | Drafter regressed for 31 min |
| **Deploy window overlapped with Mei's peak** | No deploy-window guard; deploys are allowed 24/7 | Mei's worst 12 min of feedback happened mid-incident |
| **Customs cron had no failure alert** | Non-revenue-critical job; never wrote the alert | Retrieval silently broken for 6 hr before the incident |

### 5.1 What the circuit breaker caught vs missed

The circuit breaker was tripped for 2 minutes during the deploy (normal pattern: brief spike while the new model loads), recovered, and then was "open" for the first 4 drafts. It correctly **did not catch** the hallucination because the hallucinated drafts did not throw an exception — they returned HTTP 200 with bad content. The circuit breaker catches **liveness failures**, not **quality failures**. The eval set in CI is the layer that catches quality failures before deploy.

---

## 6. The fix (the eval set in CI)

### 6.1 The PR (merged week 11, day +1)

```yaml
# .github/workflows/eval.yml
name: eval-set
on:
  pull_request:
    paths:
      - 'service/**'
      - 'shared/eval_set.jsonl'
      - 'shared/style-guide.md'

jobs:
  eval:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r service/requirements.txt
      - name: Run eval set
        run: |
          cd service
          python3 eval.py \
            --set ../shared/eval_set.jsonl \
            --baseline ../shared/baseline.jsonl \
            --threshold 0.05 \
            --report eval_report.md
      - name: Upload eval report
        uses: actions/upload-artifact@v4
        with:
          name: eval-report
          path: service/eval_report.md
      - name: Fail on regression
        run: |
          if grep -q "REGRESSION" service/eval_report.md; then
            echo "::error::Eval set regression > 0.05 on any metric"
            exit 1
          fi
```

**Behavior change:** any PR that touches `service/`, `shared/eval_set.jsonl`, or `shared/style-guide.md` now runs the eval set as a CI gate. A regression > 0.05 on any metric fails the PR. The deploy pipeline (`actions/deploy.yml`) is unchanged but now blocks on the eval gate.

### 6.2 The other 2 fixes

**Fix 2 — deploy-window guard:**

```python
# service/deploy.py
from datetime import datetime, timezone
import pytz

SGT = pytz.timezone("Asia/Singapore")
PEAK_START = 14  # 14:00 SGT (Mei's peak hours)
PEAK_END = 16    # 16:00 SGT

def is_peak_hour() -> bool:
    now = datetime.now(SGT).hour
    return PEAK_START <= now < PEAK_END

def deploy_v2(...):
    if is_peak_hour():
        raise DeployBlockedError(
            f"Deploys blocked 14:00-16:00 SGT (Mei's peak). "
            f"Use --force to override."
        )
    ...
```

**Fix 3 — cron failure alert:**

```yaml
# monitoring/alerts.yml
- alert: ShipmentCronStale
  expr: time() - shipment_cron_last_success_timestamp_seconds > 3600
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Shipment cron hasn't succeeded in > 1h"
    runbook: "https://runbook.pf.internal/data-stale"
```

These 3 fixes are **not arbitrary**. Each maps to a layer of the causal chain (CI gap → deploy window → data staleness). A principal FDE writes fixes at the layer where they're structurally guaranteed to prevent the regression class, not at the layer of the most-recent symptom.

---

## 7. Action items (with owners and dates)

| # | Action | Owner | Deadline | Status (60-day check) |
|---|---|---|---|---|
| 1 | Move eval set into CI; fail on regression > 0.05 | FDE | 2026-W11 Fri | ✅ Done (PR #251 merged) |
| 2 | Add deploy-window guard (14:00-16:00 SGT) | FDE | 2026-W11 Fri | ✅ Done (PR #252) |
| 3 | Add cron-failure alert (`ShipmentCronStale`) | Daniel | 2026-W12 Mon | ✅ Done (PR #253) |
| 4 | Add breaker-exercised-after-deploy hook (force 1 draft through after deploy, log faithfulness) | Daniel | 2026-W13 Mon | ✅ Done (PR #258) |
| 5 | Mei re-reads runbook; refresh rollback procedure | Mei | 2026-W13 Mon | ✅ Done (runbook signed) |
| 6 | Public postmortem published (this document) | FDE | 2026-W11 Fri | ✅ Done (this file) |
| 7 | Add "what changes if Singapore becomes our secondary lane" to scenario-lift.md | FDE | 2026-W14 | ✅ Done |

**All 7 action items closed in < 14 days.** This is what a fast-iterating FDE engagement looks like.

### 7.1 The 30/60/90-day follow-up

| Check | Findings |
|---|---|
| **30 days** | 0 SEV-1 incidents. Eval CI gate has caught 1 regression (a typo in the `__init__.py` import) — would have been a SEV-1 in week 11. CI gate paid for itself in < 4 weeks. |
| **60 days** | 0 SEV-1, 1 SEV-2 (a Mei-side copy-paste error — not the drafter's fault). Mei's thumbs-up rate stays at 82%. Bill at $0.49/wk. |
| **90 days** | Eval CI gate has caught 3 regressions total (1 typo, 1 chunked-policy bug, 1 RRF hyperparameter drift). The gate is doing its job. |

---

## 8. Lessons (the 5 things a principal FDE takes away)

### 8.1 The eval set is the gate

Every change that affects the prompt, the retriever, or the model must pass the eval set before merging. **A unit test that doesn't exercise the prompt is not enough.** Unit tests check code; the eval set checks behavior. They are not substitutes.

### 8.2 The breaker is a backstop, not the primary defense

The circuit breaker catches **liveness failures** (5xx, timeout) but it does not catch **quality failures** (200 with bad content). The eval set in CI catches quality failures before deploy. The breaker catches them after deploy. **Both are necessary; neither is sufficient.**

### 8.3 Incidents are inevitable; recovery time is the score

Mei will see a hallucination again — the eval set can't anticipate every prompt edge case, and the LLM is non-deterministic by nature. The MTTR (38 min in this case) is what matters. The eval set + the runbook + the rollback procedure are what make recovery cheap. **The recovery time is the operationally-meaningful SLO.**

### 8.4 The postmortem is a public artifact

This document is published internally (PacificFreight) and externally (in the case studies folder of this curriculum). **The point is not to assign blame** — the prompt change was correct, the "in Ho Chi Minh City" string is what Mei prefers — but to teach the team how to respond. A postmortem that names individuals is a punishment document; a postmortem that names systems is a learning document. **The latter is what survives.**

### 8.5 The deploy window matters

Deploys during Mei's peak hours (14:00-16:00 SGT) amplify any incident by stacking it on top of the user's busiest window. **A 14:00-16:00 deploy block is cheap insurance** that costs 0 engineering effort and reduces the SEV-1 candidate rate by an estimated 40%.

---

## 9. References

- **The eval-set-in-CI pattern**: Google SRE Book ch. 27 ("Reliable Product Launches at Scale"), ch. 17 ("Eliminating Toil").
- **The blameless-postmortem template**: Kripa Krishnan (formerly Google), "The Postmortem: Learning from Failure," SREcon14 Americas.
- **The 5-Whys technique**: original Ohno (Toyota Production System); adapted for software by Allspaw (2008) "Searching for the Root Cause."
- **Severity taxonomy**: derived from Atlassian's incident-severity definitions, Jira Service Management docs, and PagerDuty's "Major Incident Management" reference.
- **PacificFreight runbook**: `course/ai-fde/phase-3-deployment/consulting/runbook.md` — Section 4 ("Incident response"), Section 5 ("On-call rotation").
- **The PR that fixed this**: PR #251 (`course/ai-fde/.github/workflows/eval.yml`).
- **The baseline file**: `course/ai-fde/phase-2-core-build/shared/baseline.jsonl` (the eval-set baseline used by the CI gate).
