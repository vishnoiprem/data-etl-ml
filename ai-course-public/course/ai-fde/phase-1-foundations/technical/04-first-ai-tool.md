# Lesson 04 — The First AI Tool (Phase 1 Capstone)

> **You finish this lesson and you have the Phase 1 deliverable.** 45 minutes. One file, ~150 lines.

By the end of this lesson you have a CLI — **`pf-reply`** — that:

1. Reads an inbound email (file or stdin)
2. Extracts the shipment ID (regex first, LLM as fallback)
3. Looks the shipment up in the local tracker
4. Drafts a reply in PacificFreight's voice (lesson 03's LLM client + `shared/style-guide.md`)
5. Prints the draft to stdout for the CS person to copy-paste into Gmail
6. **Always works in mock mode** so you can demo it on a plane

This is the tool. Phase 1 is done when you can demo this to PacificFreight's ops manager and they say *"send me the GitHub link"*.

---

## 🎯 You will build

```bash
# 1. Read an email from a file
$ python3 technical/04-first-ai-tool.py --email ../shared/sample-emails.md --shipment PF-1001
[DRAFT for PF-1001 — delivered]
Hi Aisha,

Your shipment PF-1001 was delivered on 7 October 2026...

— Linh at PacificFreight

# 2. Read from stdin
$ echo "Where is PF-1003? I am Mei Lin" | python3 technical/04-first-ai-tool.py
[no --shipment flag — extracted from text: PF-1003]
[DRAFT for PF-1003 — held_customs]
Hi Mei Lin,
...

# 3. Shipment ID missing — the tool asks the human
$ python3 technical/04-first-ai-tool.py --email ambiguous-email.md
[could not find a shipment ID in the email]
Please ask the customer to reply with their PF-XXXX reference, then re-run with --shipment.

# 4. JSON output for piping into other tools
$ python3 technical/04-first-ai-tool.py --email ../shared/sample-emails.md --shipment PF-1003 --json
{"shipment_id": "PF-1003", "status": "held_customs", "draft": "Hi Mei Lin,...", "model": "mock-deterministic-v1", "cost_usd": 0.0}
```

## 🧠 Concept (5 min)

This tool is the FDE loop in code form:

```
       ┌──────────────────────────────────────────────────────┐
       │                                                      │
   ┌───▼────┐   regex     ┌────────┐   lookup   ┌──────────┐  │
   │ email  ├────────────►│  ID?   ├───────────►│ shipment │  │
   │ input  │             │        │            │  data    │  │
   └────────┘             └────┬───┘            └─────┬────┘  │
                              │ no                   │       │
                              ▼                      ▼       │
                       ┌────────────┐         ┌─────────────┐ │
                       │  LLM to    │         │ prompt +    │ │
                       │  extract   │         │ LLM draft   │ │
                       └─────┬──────┘         └──────┬──────┘ │
                             │                       │       │
                             └──────────┬────────────┘       │
                                        ▼                    │
                                  ┌───────────┐              │
                                  │  draft to │              │
                                  │  stdout   │              │
                                  └───────────┘              │
       │                                                      │
       └──────────────────────────────────────────────────────┘
```

Five components, all in one file. None of them is novel on its own. **The FDE skill is putting them together so the customer can run the result without you in the room.**

The five components:

1. **Email reader** — file or stdin. ~10 lines.
2. **ID extractor** — regex for the easy 80% (`PF-\d{4,}`), LLM for the 20% where the customer wrote it differently. ~20 lines.
3. **Tracker lookup** — `load_shipment` from lesson 01, copy-pasted. ~15 lines.
4. **Reply drafter** — `complete()` from lesson 03, with a system prompt that includes the style guide. ~30 lines.
5. **Output formatter** — text by default, `--json` for piping. ~10 lines.

Plus 20-30 lines of `argparse` and a docstring. Total ~150 lines. Read it top-to-bottom in 5 minutes.

## 🛠️ Build It (35 min)

The full file is `technical/04-first-ai-tool.py`. Read the file once. Then we walk through the 5 components and what each one teaches you.

### Component 1 — Email reader (input handling)

```python
def read_email(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")
```

> **FDE lesson:** every tool you build will have an input. Make it work with stdin (`-` or no arg), a file path, or both. The CS person will pipe emails from Gmail's "raw message" feature; you don't want them to have to retype.

### Component 2 — ID extractor (regex + LLM fallback)

```python
SHIPMENT_ID_RE = re.compile(r"\bPF[-\s]?\d{4,5}\b", re.IGNORECASE)

def extract_id(text: str) -> str | None:
    """Try regex first; only call the LLM if regex fails."""
    m = SHIPMENT_ID_RE.search(text)
    if m:
        return m.group(0).upper().replace(" ", "").replace("-", "-")
    return None
```

The regex catches `PF-1003`, `PF1003`, `PF 1003`, `pf-1003` — all the formats in `shared/sample-emails.md`. Normalize to `PF-XXXX`.

When the regex fails (email 3: "I think the booking reference starts with PF-10"), the LLM extracts. **The mock does not implement the LLM fallback** — it returns `None` and tells the human to ask the customer. This is honest: in production you'd add the LLM fallback; in Phase 1 you show the customer the failure mode and they tell you to ship it.

> **FDE lesson:** the regex catches 80% of cases. The LLM catches another 15%. The last 5% are unfixable. Show the customer the 80% and ask if it's worth chasing the 15%. They will almost always say *"no, ship it."*

### Component 3 — Tracker lookup (from lesson 01)

```python
def load_shipment(tracker_path: Path, shipment_id: str) -> Shipment | None:
    """Look up a shipment by ID. Returns None if not found."""
    with tracker_path.open() as fh:
        data = json.load(fh)
    target = shipment_id.upper().strip()
    for s in data["shipments"]:
        if s["id"].upper() == target:
            return Shipment(...)
    return None
```

> **FDE lesson:** in Phase 2 this becomes a call to the real PHP tracker's API. In Phase 1, the JSON file IS the tracker. The function signature does not change. The customer can read your code today and understand what Phase 2 will look like.

### Component 4 — Reply drafter (the LLM call)

The system prompt loads the style guide at startup. The user prompt contains the email + the shipment status. The model is told to output **only the reply**.

```python
STYLE_GUIDE = (Path(__file__).parent.parent / "shared" / "style-guide.md").read_text()

SYSTEM_PROMPT = f"""You are drafting customer-service emails for PacificFreight Co.

You MUST follow this style guide:

{STYLE_GUIDE}

You will be given:
1. The customer's inbound email.
2. The current shipment status from the tracker.

Output ONLY the reply text, with no preamble, no "Here's a draft:", and no quotes.
"""
```

The user prompt:

```python
def build_user_prompt(email_text: str, s: Shipment) -> str:
    return f"""Customer email:
---
{email_text}
---

Shipment in tracker:
- ID: {s.id}
- Status: {s.status}
- Last event: {s.last_event}
- Last event at: {s.last_event_at}
- Action required: {s.next_action_required or "(none)"}

Draft the reply."""
```

> **FDE lesson:** the system prompt is the *configuration* of your tool. When the customer says "the replies sound too formal," you change the system prompt (or the style guide it points to), not the code. This is why the style guide is a separate file.

### Component 5 — Output formatter

```python
def format_text(result: dict) -> str:
    return f"""[DRAFT for {result['shipment_id']} — {result['status']}]
{result['draft']}
"""

def format_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)
```

Two output modes. The CS person uses text (copy-paste into Gmail). The FDE uses `--json` to pipe into a script that opens Gmail drafts automatically (Phase 2).

### Putting it all together

The `main()` function is **40 lines of orchestration**:

1. Parse args (`--email`, `--shipment`, `--tracker`, `--json`, `--rep`).
2. Read the email.
3. Extract the ID (or use the one from `--shipment`).
4. If no ID found, print a clear error and exit 3.
5. Look up the shipment. If not found, exit 4.
6. Build the system + user prompts.
7. Call `complete()` from lesson 03.
8. Format the output.
9. Print to stdout. Exit 0.

The function is in the file — read it. Every line is doing exactly one thing.

### Run the demo on every sample email

Once the CLI works, the most valuable thing you can do is run it on **all 10 sample emails** in `shared/sample-emails.md`. For each, ask:

1. Did the tool find the right shipment ID?
2. Does the draft follow the style guide?
3. Does the tone match the customer's tone?
4. Did the tool refuse to answer things it shouldn't?

> **FDE lesson:** the 10 sample emails are your **regression test set**. When you change a prompt, run all 10. If a previously-passing email starts failing, you broke something. This is the simplest possible eval, and it is how the FDE ships without a 100-person ML team.

You are looking for **4 out of 5 correct** before you demo this to PacificFreight. Anything worse and you ship a tool that embarrasses them.

## 🏛️ FDE Lens — the one question to ask the client

> *"Would you like me to demo this with a real LLM call on your network, or in mock mode so you can see exactly what the tool would produce today without me spending API budget?"*

The answer tells you three things:

- How serious they are about the engagement (real-call = they expect to ship soon)
- Whether they have a procurement-approved API key yet (if not, mock mode is the only option)
- Whether their network can reach the LLM provider (some regulated networks block external LLM APIs; the mock is your escape hatch)

A second question, asked on day 5 of the engagement:

> *"In the first 10 replies the tool drafts, how many would you send as-is vs. how many would you edit? Target is 80% as-is. If we're below 50%, we have a prompt problem, not a tool problem."*

That number — **the as-is ratio** — is the most important metric in the engagement. The whole point of the tool is to cut the CS person's time. If they have to rewrite every draft, you've added a step, not removed one.

## 🌙 Reflect

Write 5-8 sentences:

1. Why does the regex catch the easy 80% and the LLM catch the 15%? Why not just use the LLM for everything?
2. The style guide is loaded from a file at startup, not embedded in the source. Why?
3. The CLI returns different exit codes for different failures (3 = no ID, 4 = no shipment). When would you actually use those exit codes?
4. If you had to demo this to PacificFreight on Monday, what would you change between now and then?
5. What is the **as-is ratio** target for this tool, and how would you measure it in week 1?

**What's next** — Phase 1 is done. The next move is one of:

- **The Consulting Track** — go back and build the documents (1-pager, solution outline) that justify this tool to a real client.
- **`course/practice/level-1-foundations/`** — when you want deeper architect thinking on what you just built.
- **`course/hardcode/level-1-llm-foundations/01-multi-model-async-router.py`** — when you want the 1000-line production version (with batching, circuit breakers, dedup, Prometheus).
- **`course/capstone-starters/01-ai-doc-qa/`** — the natural Phase 2 build for PacificFreight (replace the JSON tracker with the real API, add a web UI, add eval).

You finished Phase 1. The deliverable is the tool on your laptop and the story you can tell about it.
