# L6.10: Debugging the production agent — the 3am playbook

> **FDE framing in one line:** debugging a production agent at 3am is a 5-step playbook: reproduce (replay the audit log), isolate (which guardrail fired), diagnose (root cause), fix (the smallest change that resolves), verify (the regression check). The audit log is the artifact; the playbook is the discipline.

## The 3 things you'll learn

1. The 5-step debugging playbook: reproduce, isolate, diagnose, fix, verify. The discipline is the same for every incident.
2. The 3 debugging artifacts: the audit log (the timeline), the per-request trace (the run), the eval set (the regression check). Each artifact answers a different question.
3. The "postmortem as a public artifact" pattern: the postmortem is the artifact that turns a 3am incident into a permanent improvement. The customer reads it; the team learns from it; the FDE builds the runbook from it.

## Concept

Debugging a production agent at 3am is the FDE's most stressful and most important skill. The agent is a black box from the customer's perspective; the FDE's job is to turn it into a glass box. The 5-step playbook is the discipline; the 3 artifacts are the tools. **The candidate who can name the playbook + the artifacts is the candidate who can be on-call.**

The 5-step debugging playbook:

1. **Reproduce.** Replay the audit log to see exactly what happened. The audit log records every step: turn, event, tool, args, result, cost, tokens. The FDE searches the log by request_id, by tenant, by error category. The reproduction is the first step because it confirms the bug is reproducible (and not a flake).
2. **Isolate.** Identify which guardrail fired. The 5 guardrails are: loop detector, schema validator, cost ceiling, idempotency, audit log. The isolation is "the cost ceiling fired at turn 7" or "the schema validator returned a violation on the 3rd tool call." The isolation narrows the search.
3. **Diagnose.** Find the root cause. Common root causes: (a) the model emitted a malformed tool call (model issue), (b) the tool returned an unexpected error (tool issue), (c) the system prompt is ambiguous (prompt issue), (d) the eval set is incomplete (eval issue), (e) the deployment has a config drift (deployment issue). The diagnosis is the hardest step; it requires reading the model output, the tool trace, and the system prompt together.
4. **Fix.** Apply the smallest change that resolves the issue. Common fixes: (a) update the system prompt to clarify the tool boundary, (b) add a fallback tool, (c) tighten the schema, (d) lower the cost ceiling, (e) add a guardrail. The fix is shipped as a PR; the PR is reviewed by another FDE; the PR is deployed to staging first.
5. **Verify.** Run the regression check. The new version runs against the eval set; the metrics must be ≥ the old metrics. The fix is also tested against the specific case that caused the incident. The verify is the gate; if the regression fails, the fix is reverted.

The 3 debugging artifacts:

1. **The audit log (the timeline).** The structured log of every step in the agent run. The FDE searches the log by request_id, by tenant, by error category. The audit log is the timeline; it answers "what happened when."
2. **The per-request trace (the run).** The OpenTelemetry trace of the full agent run. The FDE replays the trace in Jaeger / Honeycomb to see the LLM call latency, the tool call latency, the cost per step. The trace is the run; it answers "where did the time go."
3. **The eval set (the regression check).** The list of (input, expected output) tuples that defines what good behavior looks like. The FDE runs the new version against the eval set; if the metrics drop, the fix is reverted. The eval set is the regression check; it answers "did the fix break anything else."

The "postmortem as a public artifact" pattern is the recognition that the postmortem is the artifact that turns a 3am incident into a permanent improvement. The postmortem is written in the style of GitHub's status page: timeline, root cause, impact, remediation, lessons learned. The postmortem is published internally; the customer reads it; the team learns from it; the FDE builds the runbook from it. **The postmortem is the FDE's contribution to the team's institutional knowledge; without it, the next incident is a new surprise.**

## The pattern

The 5-step playbook in action (the 3am scenario):

```python
# 3am: PagerDuty alert: "agent success rate < 90% for the last hour"
# Step 1: Reproduce
audit_log = query_audit_logs(tenant="mei", start=time.time() - 3600, end=time.time())
failing_requests = [r for r in audit_log if r["error"]]
# Result: 12 failing requests, all on the same tool: refund.create

# Step 2: Isolate
# Guardrail that fired: schema validator (refund.create returned "schema_violation: missing idempotency_key")
isolated_guardrail = "schema_validator"
# Step that failed: turn 3 of the agent run
failed_step = 3

# Step 3: Diagnose
# Read the model output for the failing requests
model_outputs = [r["model_output"] for r in failing_requests]
# Diagnosis: the model is calling refund.create WITHOUT the idempotency_key
# Root cause: the system prompt does NOT mention that idempotency_key is required
# The model is omitting it because the system prompt is silent on the requirement

# Step 4: Fix
# Update the system prompt to require idempotency_key
new_system_prompt = update_guardrail(
    old=CS_DRAFTER_SYSTEM_PROMPT,
    guardrail_id=1,
    new_text="refund.create requires an idempotency_key (e.g., '<shipment_id>-<amount>-<date>'). "
             "Generate a unique key for each call; never reuse a key.",
)
# Ship as a PR; review by another FDE; deploy to staging first.

# Step 5: Verify
new_metrics = run_eval(new_agent, EVAL_SET)
assert new_metrics["answer_relevance"] >= BASELINE_METRICS["answer_relevance"] - 0.02
assert new_metrics["success_rate"] >= 0.95
# Test the specific case
result = new_agent.run("Refund $50 for PF-1003")
assert "idempotency_key" in result["trace"][2]["args"]  # Turn 3 includes the key
# Deploy to production
```

The 3 debugging artifacts (the FDE's toolkit):

```python
DEBUGGING_ARTIFACTS = {
    "audit_log": {
        "where": "CloudWatch / Loki / Datadog",
        "what": "Every step in the agent run: turn, event, tool, args, result, cost, tokens",
        "question_answered": "what happened when?",
        "query": 'request_id="req-abc123" OR tenant="mei" AND error IS NOT NULL',
    },
    "per_request_trace": {
        "where": "OpenTelemetry / Jaeger / Honeycomb",
        "what": "The full agent run: system prompt, messages, LLM calls, tool calls, observations",
        "question_answered": "where did the time go? where did the cost go?",
        "query": 'service="pf-agent" trace_id="abc123"',
    },
    "eval_set": {
        "where": "Git repo (course/practice/level-5-agents/eval_set.jsonl)",
        "what": "100 (input, expected output) tuples that define what good behavior looks like",
        "question_answered": "did the fix break anything else?",
        "query": "python -m pytest test_regression.py --eval-set=eval_set.jsonl",
    },
}
```

The postmortem template:

```markdown
# Postmortem: Agent success rate dropped to 88% for 1 hour on 2026-10-10

## Timeline (UTC)
- 02:14: First failure recorded: refund.create schema_violation (missing idempotency_key)
- 02:15: PagerDuty alert: success rate < 90%
- 02:18: FDE on-call (Prem) acknowledges
- 02:25: Root cause identified: system prompt does not require idempotency_key
- 02:35: Fix shipped to staging
- 02:42: Regression check passes
- 02:50: Fix deployed to production
- 03:00: Success rate back to 98%

## Impact
- 12 customer runs failed
- 0 customers churned
- $0 lost revenue (all runs were non-urgent)

## Root cause
The system prompt for the CS-drafter agent did not explicitly require the `idempotency_key` argument for `refund.create`. The model was emitting the call without the key; the schema validator correctly rejected it; the model received the violation and retried — but the schema violation was returned as a model observation, not a hard error, so the loop continued to fail.

## Why didn't we catch this earlier?
- The eval set did not include a case that exercises the idempotency_key requirement
- The contract tests for the system prompt did not check for "idempotency_key" in the prompt

## Remediation
- Updated the system prompt to require `idempotency_key` for `refund.create`
- Added an eval set case that exercises the idempotency_key requirement
- Added a contract test that asserts "idempotency_key" appears in the system prompt

## Lessons learned
- The schema validator is a safety net, not a substitute for a clear system prompt
- The eval set is the spec; missing cases = missing requirements
- The on-call playbook worked; the 35-minute MTTR is within SLA
```

The pattern that wins interviews is the "5-step playbook + 3 artifacts + postmortem" pattern. The candidate who says "I debug with a 5-step playbook (reproduce, isolate, diagnose, fix, verify); I use 3 artifacts (audit log for the timeline, trace for the run, eval set for the regression); I write a postmortem for every incident; the postmortem turns the 3am surprise into a permanent improvement. The wrong choice is to skip the reproduce step (you fix the wrong thing). The right choice is the playbook + the artifacts + the postmortem" is the candidate who demonstrates the debugging-mindset.

## Code or example

The 3am incident response (the full sequence):

```python
# 3am incident response
def respond_to_incident(alert: dict) -> dict:
    """The 3am playbook, automated."""
    # Step 1: Reproduce
    failing_logs = query_audit_logs(filters=alert.get("filters"))
    reproduction = {
        "count": len(failing_logs),
        "common_pattern": find_common_pattern(failing_logs),
    }

    # Step 2: Isolate
    guardrail = reproduction["common_pattern"]["guardrail"]
    step = reproduction["common_pattern"]["step"]

    # Step 3: Diagnose
    diagnosis = diagnose_root_cause(failing_logs, guardrail, step)
    # Returns: {root_cause: "system prompt missing idempotency_key requirement", confidence: 0.95}

    # Step 4: Fix
    fix_proposal = generate_fix(diagnosis)
    # Returns: {type: "prompt_update", old: "...", new: "..."}

    # Step 5: Verify
    new_agent = apply_fix(AGENT, fix_proposal)
    new_metrics = run_eval(new_agent, EVAL_SET)
    passes = all(new_metrics[k] >= BASELINE_METRICS[k] - 0.02 for k in BASELINE_METRICS)

    if passes:
        deploy(new_agent)
        return {"status": "fixed", "fix": fix_proposal, "mttd_min": 5, "mttr_min": 35}
    return {"status": "regression_detected", "fix": fix_proposal, "metrics": new_metrics}
```

The on-call runbook (the FDE's reference):

```markdown
# PacificFreight Agent On-Call Runbook

## Alert: cost_per_run_p95 > 2× baseline
1. Check the audit log for high-cost runs
2. Identify the tool that drove the cost (likely a long-running web_search loop)
3. Lower the cost ceiling temporarily (0.50 → 0.25)
4. Add a loop detector alert
5. Page the FDE on-call if not resolved in 30 min

## Alert: success_rate < 95%
1. Check the audit log for the most common error
2. Identify the guardrail that fired (parse, schema, cost, tool, model)
3. Diagnose the root cause (model output, tool error, system prompt)
4. Apply the fix; run the regression check
5. Page the senior FDE if not resolved in 60 min

## Alert: error_rate_by_category.spike
1. Identify the category that spiked
2. Apply the matching recovery strategy:
   - transient: retry with backoff; if persistent, page the upstream vendor
   - permanent: check the policy file; if customer-side, escalate
   - model: check the model status page; if vendor-side, switch to fallback model
   - tool: check the tool's status; if persistent, enable the fallback tool
3. Page the FDE on-call if not resolved in 30 min
```

## Production addendum

The debugging question is the answer to "how do you debug an agent at 3am." The 60-second script:

> "5-step playbook: reproduce (replay the audit log), isolate (which guardrail fired), diagnose (root cause), fix (smallest change that resolves), verify (regression check). 3 artifacts: audit log (the timeline), per-request trace (the run), eval set (the regression check). **The postmortem is the artifact that turns a 3am incident into a permanent improvement.** The wrong choice is to skip the reproduce step (you fix the wrong thing). The wrong choice is to skip the postmortem (the next incident is a new surprise). The right choice is the playbook + the artifacts + the postmortem + the runbook."

This is the difference between a candidate who says "I debug agents" and a candidate who says "5-step playbook, 3 artifacts, postmortem as a public artifact, on-call runbook." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-1-foundations/README.md` — the debugging playbook.
- **Reference implementation**: `course/ai-fde/phase-3-deployment/consulting/runbook.md` — the production runbook.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — debugging as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/case-studies/engagement-3-postmortem.md` — the canonical postmortem case study.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/company-experiences/anthropic-fde-customer-simulation.md` — the customer-simulation round is the 3am scenario in costume.

## The 3 questions this lecture preps you for

1. **"How do you debug an agent at 3am?"** Answer: 5-step playbook. Reproduce (replay the audit log). Isolate (which guardrail fired). Diagnose (root cause). Fix (smallest change that resolves). Verify (regression check). 3 artifacts: audit log (timeline), per-request trace (the run), eval set (regression check).
2. **"What is the postmortem as a public artifact pattern?"** Answer: every incident gets a postmortem in the style of GitHub's status page: timeline, root cause, impact, remediation, lessons learned. The postmortem is published internally; the customer reads it; the team learns from it; the FDE builds the runbook from it. **The postmortem turns a 3am surprise into a permanent improvement.**
3. **"What are the 3 debugging artifacts?"** Answer: (1) audit log (the timeline — what happened when, queried by request_id, tenant, error category), (2) per-request trace (the run — where did the time and cost go, replayed in Jaeger/Honeycomb), (3) eval set (the regression check — did the fix break anything else). The 3 artifacts answer 3 different questions; the FDE needs all 3.

## Read next

`S7-n8n-practical/L7-1-the-n8n-platform.md` — Section 7 dives into the n8n practical: how to build agentic automations with n8n's visual workflow editor. n8n is a low-code alternative to the 200-line stdlib agent; it's the right tool for non-engineering teams and for rapid prototyping. The 7 ingredients + the 5 guardrails apply; the implementation is visual instead of code.