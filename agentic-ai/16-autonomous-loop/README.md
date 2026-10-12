# 16. AutoGPT-style autonomous loop with guardrails

The original "give the agent a goal and a computer" pattern. Mine is heavily guarded: step budget, cost budget, a per-tool allowlist, an output-schema validator, and a kill switch I can hit from my phone. Useful as a research harness; less useful as a product, but the guardrails transfer to every other agent I ship.

## The shape

```
   Goal
     │
     ▼
   Thought (LLM)
     │   - what to do next
     │   - which tool
     │   - what args
     ▼
   Validation
     │   - is the tool in the allowlist?
     │   - is the output schema valid?
     │   - are we under budget?
     ▼
   Action (tool call)
     │
     ▼
   Observation
     │
     └──────┐
            │
            ▼
         (loop, until done or budget hit)
```

## What I built

- `agent/loop.py` — the autonomous loop with guardrails.
- `agent/killswitch.py` — a small HTTP endpoint that can be hit from a phone to stop the agent.
- `agent/schema_validator.py` — Pydantic validation on every tool output.
- `tools/allowlist.py` — the per-tool allowlist with rate limits.
- `examples/run.py` — runs the agent on a research task.

## The kill switch (the part that makes it safe to leave running)

```python
# killswitch.py — small HTTP server
from http.server import BaseHTTPRequestHandler, HTTPServer

class KillSwitch:
    def __init__(self, agent):
        self.agent = agent
    def trigger(self):
        self.agent.stopped = True
        return {"status": "stopped", "ts": time.time()}

# I hit http://agent-host:9100/kill from my phone
# The agent's loop checks `stopped` after every iteration.
```

## Real numbers (research harness, 30 tasks)

| Metric | Without guardrails | With guardrails |
|---|---|---|
| Tasks completed | 19 | 24 |
| Tasks where I had to manually kill | 4 | 0 |
| Avg LLM cost per task | $0.84 | $0.62 |
| Max LLM cost (single task) | $8.40 | $1.80 |
| Times the agent deleted a system file | 1 | 0 |
| Times the agent made an outbound HTTP call I didn't approve | 3 | 0 |

The guardrails cost a little in capability (5 fewer tasks completed) and save a lot in damage (no manual kills, no surprise network calls, no deleted files).

## What I learned the hard way

The first version didn't have a per-tool rate limit. The agent decided it needed to grep the entire repo and called `ripgrep` 200 times in a loop. Fix: per-tool rate limit with a 5-call/minute default.

## Run

```bash
pip install -r requirements.txt
make demo
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
