# Capstone presentation rehearsal checklist

> **Use this checklist in the 10 minutes BEFORE the live demo.**
> Go through it top to bottom. If any item fails, fix it before
> the panel arrives. The capstone presentation script
> ([`CAPSTONE-PRESENTATION.md`](./CAPSTONE-PRESENTATION.md))
> is what you say during the demo; this checklist is what you
> do BEFORE the demo.

## 10 minutes before

### 1. Servers running

- [ ] `uvicorn service.app:app --host 0.0.0.0 --port 8000`
  responding (`curl http://localhost:8000/health` → 200)
- [ ] `python3 slm/serve.py --back-end mock` running on port
  8001 (`curl http://localhost:8001/health` → 200)
- [ ] `ollama` running with `pf-drafter` model imported
  (`ollama list` shows `pf-drafter`)
- [ ] (If you have a real GPU) `python3 slm/serve.py --back-end ollama`
  on a second port 8002

### 2. Eval set green

- [ ] `cd service && python3 eval.py --set ../shared/eval_set.jsonl
  --report /tmp/eval_report.md` runs without error
- [ ] All 4 metrics are above the bar (faithfulness > 0.85,
  ansrel > 0.70, ctxp > 0.85, ctxr > 0.85)
- [ ] No regressions vs the baseline

### 3. Dashboard loaded

- [ ] Prometheus UI at `http://localhost:9090` (or your custom
  dashboard) is open in a browser tab
- [ ] The PacificFreight drafter's metrics are showing:
  - `pf_drafts_total` (should be > 1000 by now)
  - `pf_thumbs_up_rate` (should be ~ 0.82)
  - `pf_p95_latency_ms` (should be ~ 1800)
  - `pf_weekly_cost_usd` (should be ~ 0.50)

### 4. Sample emails pre-loaded

- [ ] `cat /tmp/sample_emails.md` shows 3 emails:
  1. "Hi, where is my shipment PF-1003? — Mei Lin"
  2. "PF-1002 stuck in transit?? Please advise."
  3. "I'd like a refund for PF-1003. Charged twice."
- [ ] All 3 are ready to paste into the Swagger UI's `/draft`
  textarea

### 5. SEV-1 scenario pre-loaded

- [ ] The week-11 hallucination scenario is in
  `case-studies/engagement-3-postmortem.md` and ready to open
- [ ] The 5-question "FDE has left" test answers are in
  `case-studies/engagement-5-handoff.md` and ready to open

### 6. Cost model ready

- [ ] `case-studies/engagement-4-slm-cost.md` is in a tab, scrolled
  to the cost model section
- [ ] The numbers ($0.50/week GPT-4o-mini, $0.19/week SLM + fallback,
  $3.78/month at 10× volume) are visible

## 5 minutes before

### 7. Browser tabs in order

- [ ] Tab 1: FastAPI Swagger UI (`http://localhost:8000/docs`)
- [ ] Tab 2: Prometheus UI (or custom dashboard)
- [ ] Tab 3: `engagement-1-pf-drafter.md` (the flagship story)
- [ ] Tab 4: `mcp_policies.yaml` (for the "add a new tool" demo)
- [ ] Tab 5: `engagement-4-slm-cost.md` (cost model)
- [ ] Tab 6: `engagement-5-handoff.md` (the 5-question test)

### 8. Terminals ready

- [ ] Terminal 1: `cd 02-multi-agent-dispatcher && python3 service/agents.py
  --case multi_shipment` ready to run
- [ ] Terminal 2: `cd 01-mcp-drafter && python3 service/mcp_server.py`
  ready to run
- [ ] Terminal 3: a shell with `curl -X POST http://localhost:8000/draft`
  ready (for fallback if the Swagger UI acts up)

### 9. Backup plans

- [ ] If the Swagger UI fails: use Terminal 3's curl command
- [ ] If uvicorn is down: `uvicorn service.app:app --host 0.0.0.0
  --port 8000 &` and wait 3 seconds
- [ ] If ollama is down: the SLM serve falls back to the mock
  back-end (this is the default — make sure the mock is configured
  correctly)
- [ ] If the eval set regresses during the demo: `git revert HEAD`
  and `docker restart pf-drafter` (the rollback procedure)

### 10. Mental check

- [ ] I'm wearing the 90-second pitch ("I build AI services that
  survive the customer") in my head
- [ ] I know which slide transitions are scripted vs improvised
- [ ] I've practiced the 5-question test answers (Daniel's,
  Mei's, Sarah's) out loud at least once
- [ ] I have water

## 1 minute before

### 11. Final smoke test

- [ ] `curl http://localhost:8000/health` → 200
- [ ] `curl http://localhost:8001/health` → 200
- [ ] `python3 -c "from service.mcp_server import MCPServer;
  print(MCPServer().list_tools().__len__())"` → 4
- [ ] `python3 service/agents.py --case single_shipment` returns
  valid JSON

### 12. Silence the noise

- [ ] Phone on silent
- [ ] Slack/email notifications off
- [ ] Background music off (if any)
- [ ] "Do not disturb" sign on the door (if in-person)

## 0 minutes — showtime

The panel is here. The 7 slides are queued. The 10 minutes start.

**Slide 1 (1 min):** The FDE pattern. "I build AI services that
survive the customer. Eval-set-as-spec, runbook-as-contract,
cost-ceiling-as-score."

**Slide 2 (3 min):** The drafter demo. 3 emails, dashboard
updating.

**Slide 3 (2 min):** The MCP server. 4 tools, RBAC, rate limit.

**Slide 4 (1 min):** The multi-agent trace.

**Slide 5 (1 min):** The SLM cost model.

**Slide 6 (1 min):** The 5-question "FDE has left" test.

**Slide 7 (1 min):** Portfolio + case studies + what I'd do
differently.

**Q&A (10 min):** Answer the 5 common questions.

**Total: 20 minutes.** (10 demo + 10 Q&A.)

The presentation script ([`CAPSTONE-PRESENTATION.md`](./CAPSTONE-PRESENTATION.md))
has the talking points for each slide.

## After the demo

### 13. Tear-down

- [ ] `kill %1 %2 %3` (or `pkill -f uvicorn`, `pkill -f "slm/serve"`)
- [ ] Save the eval report (`/tmp/eval_report.md` → `~/eval_reports/`)
- [ ] Save the dashboard screenshots (Cmd-Shift-4 on macOS)
- [ ] Send a thank-you note to the panel

## Lessons from past demos

1. **The Swagger UI always acts up.** Have a curl command ready
   in Terminal 3.
2. **The dashboard is slow.** Open it 5 minutes before, not
   30 seconds before.
3. **The eval set might regress during the demo.** If it does,
   pause, say "let me show you the rollback procedure," and run
   it. The panel will be impressed by the recovery time.
4. **The 5-question test is the strongest moment.** Don't skip it.
5. **The "what I'd do differently" slide is the second-strongest.**
   Don't skip that either. The panel wants to see self-awareness.