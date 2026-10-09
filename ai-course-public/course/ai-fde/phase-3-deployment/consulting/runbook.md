# Runbook — PacificFreight drafter

> **Owner:** Daniel (IT). **Last reviewed:** 2026-10-09. **Re-review:** every 6 months or after any SEV-1.

This is the 5-step runbook for the 4 SEV levels of the PacificFreight drafter. Each SEV has the same 5 steps: **detect → diagnose → mitigate → recover → postmortem**. The SEV-1 quick-reference card is at the top — Daniel can read it in 30 seconds while paging.

---

## SEV-1 quick-reference card (1 page)

```
SYMPTOM:  Drafter is down. Mei cannot send drafts. /draft returns 5xx for > 5 min.
DETECT:   /metrics shows pf_drafts_total{outcome="error"} rate > 0.5/s for 5 min.
          OR Mei pages: "the drafter is broken."
DIAGNOSE: 1. curl GET /circuit/state → look at "state" + "recent_transitions"
          2. If state=open:  the LLM is degraded. Check window_failures/window_n ratio.
          3. If state=closed: the LLM is fine. Check VM health, network, recent deploys.
          4. tail -100 usage.jsonl | jq 'select(.outcome=="error")'  →  look for patterns
MITIGATE: 1. If breaker open:   wait 30s for HALF_OPEN; if it succeeds, CLOSED.
          2. If VM is down:     ssh in, check docker ps, restart pf-phase2.
          3. If cost is spike:  /circuit/state window_cost_usd > $5. Pause non-essential calls.
          4. If unknown:        page FDE (Tier 4, 1-week SLA).
RECOVER:  1. After 30 min of CLOSED state, mark the SEV-1 resolved in the incident log.
          2. Write a 1-page postmortem within 48 hours.
          3. Add an ADR entry describing the change that prevents recurrence.
```

---

## SEV-1: Drafter is down (Mei cannot send drafts)

**Definition:** `/draft` returns 5xx for > 5 minutes. Mei cannot send any drafts.

### Step 1: Detect

- `/metrics` shows `pf_drafts_total{outcome="error"}` rate > 0.5/s for 5 min
- OR `/health` returns non-200
- OR Mei pages: "the drafter is broken"

### Step 2: Diagnose (90 seconds)

```bash
# 1. Is the breaker open?
curl -s http://localhost:8000/circuit/state | jq '.state, .recent_transitions[0:3]'

# 2. If breaker is closed, is the VM alive?
ssh daniel@pf-vm "docker ps | grep pf-phase2"
ssh daniel@pf-vm "docker logs pf-phase2 --tail 100"

# 3. What's the cost situation?
tail -1000 usage.jsonl | jq -s 'map(.cost_usd) | add'

# 4. Is the LLM provider down?
curl -s https://status.openai.com/ | jq '.status.description'
```

Decision tree:

- Breaker open + LLM provider down → **wait for the LLM to recover; breaker will self-recover via HALF_OPEN after 30s cooldown**
- Breaker open + LLM provider fine → **page FDE (Tier 4)**; the breaker tripped incorrectly
- Breaker closed + VM down → **restart the container** (`docker restart pf-phase2`)
- Cost spike → **see SEV-4**

### Step 3: Mitigate (5 minutes)

If the LLM is down:
- The 3-tier fallback (cache → cheaper LLM → stub) is already in place. Mei will see drafts from the cache for the ~40 near-duplicate emails/day. Other emails get the stub `[unavailable]`.
- Mei should send manual replies for the stub cases.
- Wait 30s for HALF_OPEN. If the trial call succeeds, breaker → CLOSED. Mei is back.

If the VM is down:
- `docker restart pf-phase2` (1 min)
- Verify `/health` returns 200
- Verify `/circuit/state` is CLOSED

If the cost is spiking:
- See SEV-4.

If unknown:
- Page FDE (Tier 4, 1-week SLA)
- Document the page in the incident log

### Step 4: Recover (30 minutes)

1. Wait 30 minutes of CLOSED state to confirm the SEV-1 is resolved.
2. Update the incident log: `incidents/2026-10-09-sev1.md` with start time, end time, root cause, mitigation steps.
3. Notify Mei + Sarah that the drafter is back.
4. Schedule a postmortem within 48 hours.

### Step 5: Postmortem (within 48 hours)

Template:

```markdown
# Postmortem — 2026-10-09 SEV-1

## Summary
- Start: 14:23 SGT
- End:   14:38 SGT (15 min downtime)
- Impact: 12 drafts failed; Mei sent manual replies for 4.

## Root cause
OpenAI API degraded from 14:23 to 14:34. Circuit breaker tripped
on 3 consecutive failures at 14:24. State transitioned OPEN → HALF_OPEN
at 14:25 → CLOSED at 14:35 once OpenAI recovered.

## What went well
- Breaker tripped in 1 minute, not 11.
- Cache served 3 drafts; stub served the rest.
- Mei saw `[unavailable]` instead of a hung page.

## What went wrong
- 4 drafts required manual replies.
- Mei was not paged proactively (she noticed herself).

## Action items
- [ ] Add a Slack alert when the breaker opens. (Owner: Daniel, 1 week)
- [ ] Add 5 more cache-eligible patterns from Mei's recent drafts. (Owner: FDE, 1 week)
- [ ] ADR-0018: document the breaker behavior in the runbook. (Owner: FDE, this postmortem)
```

---

## SEV-2: Hallucination spike (eval set regresses, or Mei reports 3+ thumbs-down/hour)

**Definition:** Eval set's regression check trips (`run_regression_check` flags a metric), OR Mei sends 3+ thumbs-down in 1 hour, OR a regulatory-relevant claim appears in a draft (e.g., wrong refund amount, wrong customs duty).

### Step 1: Detect

- Eval set CI run fails with `🔴 REGRESSED` on any metric
- OR `/feedback` shows 3+ thumbs-down in 1 hour
- OR Mei reports a specific hallucination: "the draft said my customer owes $500 but the actual duty is $50"

### Step 2: Diagnose (5 minutes)

```bash
# 1. Re-run the eval set locally and compare to baseline.
python3 service/eval.py eval --set shared/eval_set.jsonl \
       --baseline shared/baseline.jsonl --threshold 0.05 \
       --report eval_report.md

# 2. Look at the recent thumbs-down notes.
tail -200 usage.jsonl | jq 'select(.outcome=="feedback" and .feedback_rating==-1) | .note'

# 3. Was there a recent prompt or model change?
git log --oneline --since="2 days ago" -- service/rag.py
# Check the model's release notes if a model was upgraded.
```

Decision tree:

- Eval regressed on a known category → **roll back the recent prompt change** (git revert)
- Eval regressed without a recent change → **the LLM provider may have shipped a model update**; check provider release notes
- Mei reports a specific hallucination → **find the row, add it to the eval set, run regression**

### Step 3: Mitigate (1 hour)

1. If a recent change caused the regression: **revert the PR**. Deploy the previous version. Mei is back to the last-known-good state.
2. If the LLM provider changed: **pin the model version** in `service/app.py` (e.g., `model="gpt-4o-mini-2024-07-18"`). Re-run the eval. Confirm green.
3. If Mei reports a specific hallucination: **add 5 new eval rows** covering the failure mode. Confirm the new rows fail (the eval set is now stronger). Pick a 1-week experiment to fix them.

### Step 4: Recover (24 hours)

1. Re-run the eval set; confirm green.
2. Add the new rows to the baseline.
3. Notify Mei + Sarah: "the regression is fixed; here's the ADR."
4. Update the runbook if the mitigation revealed a gap.

### Step 5: Postmortem (within 1 week)

Same template as SEV-1. Add a section: "What rows did we miss? Are they in the eval set now?"

---

## SEV-3: P95 latency > 4s for 30+ minutes

**Definition:** `pf_draft_latency_seconds` p95 > 4s for 30 consecutive minutes. Mei is on a slow wifi, OR the LLM is degraded, OR a multi-shipment email is triggering a 2nd retrieval.

### Step 1: Detect

- Grafana alert: `histogram_quantile(0.95, rate(pf_draft_latency_seconds_bucket[5m])) > 4.0` for 30 min
- OR Mei reports: "the drafter is sluggish today"

### Step 2: Diagnose (10 minutes)

```bash
# 1. Is it Mei's network, or the service?
ssh daniel@pf-vm "ping -c 5 api.openai.com"

# 2. Is the LLM slow for everyone, or just Mei's prompts?
tail -1000 usage.jsonl | jq -s 'group_by(.user_id) | map({user: .[0].user_id, p95: (map(.latency_ms) | sort | .[length * 0.95 | floor])})'

# 3. Is the breaker close to tripping?
curl -s http://localhost:8000/circuit/state | jq '.window_n, .window_failures, .window_cost_usd'

# 4. Are there multi-shipment emails (PF-XXXX + PF-YYYY in the body)?
tail -200 usage.jsonl | jq 'select(.n_contexts > 5) | {ts, request_id, n_contexts, latency_ms}'
```

### Step 3: Mitigate (4 hours)

1. If Mei's network: **nothing to do**. The drafter is fine. Tell Mei.
2. If the LLM is slow for everyone: **wait**. The breaker will trip and route to fallback. Mei sees `[unavailable]` for new drafts; the cache serves near-duplicates.
3. If multi-shipment emails are slow: **investigate the 2nd retrieval**. May be a `service/rag.py::retrieve` bug. Open a PR with a fix; deploy Friday.
4. If unknown: **page FDE (Tier 4)**.

### Step 4: Recover (24 hours)

1. If the LLM recovered: confirm P95 < 4s in Grafana.
2. If the multi-shipment fix shipped: confirm eval set is green.
3. Notify Mei + Sarah.

### Step 5: Postmortem (within 1 week)

Same template. Add: "Did the breaker trip correctly? Did the fallback serve Mei well?"

---

## SEV-4: Cost overage (>$5/month)

**Definition:** Sum of `cost_usd` in `usage.jsonl` over the calendar month > $5.

### Step 1: Detect

- Daniel's monthly review: `awk -F'"cost_usd":' '{print $2}' usage.jsonl | awk -F',' '{sum+=$1} END {print sum}'` > $4 (alert at 80% of ceiling)
- OR a single day's cost > $1 (early warning)

### Step 2: Diagnose (1 hour)

```bash
# 1. What's the cost by user?
tail -10000 usage.jsonl | jq -s 'group_by(.user_id) | map({user: .[0].user_id, cost: (map(.cost_usd) | add), n: length}) | sort_by(.cost) | reverse'

# 2. What's the cost by day?
tail -10000 usage.jsonl | jq -s 'group_by(.ts | floor / 86400 | todate) | ...'

# 3. Is there a loop? (same request_id > 10 times in 1 hour)
tail -10000 usage.jsonl | jq -s 'group_by(.request_id) | map(select(length > 10))'
```

### Step 3: Mitigate (1 week)

1. If a single user is over: **talk to them**. Mei probably has a script running. Or someone else is using the service.
2. If a loop is detected: **the rate limiter should have caught it**. Check `pf_drafts_total{outcome="rate_limited"}` — if it's 0, the rate limiter is broken. Fix it.
3. If a model upgrade caused it: **downgrade the model** to `gpt-4o-mini` or cheaper. Re-run the eval to confirm quality holds.

### Step 4: Recover (1 week)

1. Cost returns to <$5/month trend.
2. Adjust the cost ceiling if needed (with Sarah's sign-off).
3. Update the runbook.

### Step 5: Postmortem (within 1 week)

Same template. Add: "Did the rate limiter catch it? Did the cost alert fire in time?"

---

## Incident log

Every SEV gets a row in `incidents/YYYY-MM-DD-sevN.md`. The log is append-only. The next FDE reads the log on day 1 to understand the system's failure history.

| Date | SEV | Duration | Root cause | Postmortem |
|---|---|---|---|---|
| 2026-10-09 | 1 | 15 min | OpenAI degradation | incidents/2026-10-09-sev1.md |
| (empty) | | | | |

The log is the institutional memory of the system's reliability. A log with zero entries is a sign the runbook is not being used, not a sign the system is reliable.

## Re-review schedule

- Every 6 months: Daniel re-reads the runbook end-to-end.
- After any SEV-1 or SEV-2: Daniel updates the runbook based on what he learned.
- After any FDE transition: the incoming FDE runs the fire-drill within 1 week.
