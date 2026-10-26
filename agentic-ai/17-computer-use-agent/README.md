# 17. Anthropic-style Computer Use agent

The agent sees the screen, moves the mouse, clicks, types. I built one for a legacy internal tool that has no API: read the screen with a VLM, plan the next action, execute it via Playwright, verify the result. It works 70% of the time; the other 30% is a hallucinated button that I now log and replay.

## The shape

```
   Screenshot ──▶ VLM (vision model)
                      │
                      ▼
                 Plan next action
                 ("click the 'Submit' button at x=420, y=210")
                      │
                      ▼
                 Playwright / PyAutoGUI
                      │
                      ▼
                 New screenshot ──▶ verify
```

## What I built

- `agent/perception.py` — VLM wrapper that takes a screenshot and returns structured actions.
- `agent/plan.py` — planner that takes the screenshot + the task and picks the next action.
- `agent/execute.py` — Playwright wrapper for browser actions, PyAutoGUI for desktop.
- `agent/verify.py` — post-action check: did the screen change in the expected way?
- `agent/replay.py` — every (screenshot, action, result) is logged for replay + debugging.
- `examples/legacy_tool.py` — runs the agent on the legacy internal app.

## The failure mode (the part that matters)

The 30% failure rate breaks down like this:

- 12% — VLM hallucinated a button that doesn't exist. Log: `{"reason": "no_button_at_xy", "expected": "Submit"}`. Fix: an explicit "is this button visible?" check before clicking.
- 8% — clicked the right button but the page didn't load in time. Fix: explicit wait + retry.
- 6% — modal dialog appeared that wasn't in the screenshot. Fix: a periodic "alert check" on every action.
- 4% — actual VLM error (misread the screen). No clean fix; logged for replay.

## The replay log

```python
@dataclass
class ReplayEntry:
    ts: float
    screenshot_path: str
    action: dict
    result: str
    reasoning: str

# I can replay any session: feed the screenshots to the model, see what it would do.
# When a real failure happens, I have the exact (screen, action) pair to debug.
```

## Real numbers (4 weeks, 1.2K actions on a legacy CRM)

| Metric | Value |
|---|---|
| Task completion rate | 70% |
| Avg actions per task | 14 |
| Avg time per task | 2m 22s |
| Hallucinated-button rate | 12% |
| Modal-dialog surprise rate | 6% |
| Time saved vs manual | 4.1 hours/week |

The 30% failure rate is the deal. For a non-API legacy tool, 70% automation at 4 hours/week saved is a net positive. For a high-stakes workflow (e.g., moving money), it would not be.

## Run

```bash
pip install -r requirements.txt
make demo
```

---

## What this is NOT

- **Not production-safe for high-stakes workflows.**
  The 30% failure rate is the deal. For a 4-hours/week
  saved on a legacy CRM, that's a net positive. For
  "moving money" or "filing a regulatory report,"
  it would not be. The VLM hallucinates buttons;
  modals appear unannounced; pages don't load in
  time. Plan for the 30%, not the 70%.
- **Not an API replacement.** The whole point of
  this build is that the legacy tool has *no API*.
  If the tool has an API, use it. Computer Use is
  for the last-resort case where there is no
  alternative.
- **Not a security boundary.** The agent has
  screen-level access; it can see and click
  *anything* in the browser window. If the page
  has session tokens, payment forms, or admin
  controls, the agent can act on them. The
  approval gate (in
  [`../9-terminal-agent-claude-code/`](../9-terminal-agent-claude-code/))
  is the only friction.
- **Not a one-shot agent.** The screenshot →
  action → verify loop runs once per step. A
  long task is many steps; a stuck-in-a-loop is
  the same risk as the terminal agent.

---

## Related directories

- [`../13-browser-agent-comet-style/`](../13-browser-agent-comet-style/) —
  the browser-only cousin: same shape, but
  restricted to a browser context (no desktop
  control). Safer default for web workflows.
- [`../9-terminal-agent-claude-code/`](../9-terminal-agent-claude-code/) —
  the terminal cousin: shell control instead of
  screen control. Same planner-executor shape.
- [`../11-general-agent-manus-style/`](../11-general-agent-manus-style/) —
  the general-purpose cousin: any tool in the
  allowlist, not just screen + mouse.
- [`../16-autonomous-loop/`](../16-autonomous-loop/) —
  the bounded-loop + budget + retry pattern; the
  long-task stuck-detection lives here.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
