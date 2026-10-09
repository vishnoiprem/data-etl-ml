# Lesson 01 — Python Tooling

> **The boring stuff that makes shipping possible.** 25 minutes. One tiny CLI.

By the end of this lesson you can open a terminal, create a Python project that:

- uses a virtual environment (so dependencies don't leak)
- loads secrets from a `.env` file (and **never** commits them)
- has a CLI with `--help` (so the customer can run it without you)
- has type hints on every function (so you can refactor without fear)
- runs on Python 3.11+ (so the modern AI SDKs work)

This is the smallest possible "shippable AI tool" skeleton. Everything in Phase 1 builds on it.

---

## 🎯 You will build

A 50-line Python CLI called `pf-lookup` that takes a shipment ID, reads `shared/shipments.json`, and prints the latest event. It will be the seed of the full reply-drafting tool in lesson 04.

```bash
$ python3 technical/01-python-tooling.py PF-1003
Shipment PF-1003  (Kuala Lumpur → Singapore)
Status: held_customs
Last event (2026-10-06): Held at Singapore customs — import duty invoice issued, awaiting payment.
Action: Customer to pay SGD 42.50 import duty via the link in the SMS sent on 2026-10-06.
```

## 🧠 Concept (5 min)

There are four things every AI tool you ship will need. None of them are AI. They are:

1. **A virtual environment.** `python3 -m venv .venv` (or `uv venv .venv` if you have it). This isolates your project's dependencies from every other Python project on your machine. Without it, you will eventually install two tools that want two different versions of the same library, and one of them will silently break.

2. **A `.env` file for secrets.** API keys, customer tokens, database URLs — they all go in a file called `.env` that is in your `.gitignore`. You load them in code with `python-dotenv`. You **never** put them in source. The customer will not trust you if you do.

3. **An `argparse` CLI.** Even if the tool will eventually have a web UI, a CLI is the fastest way to test it, the easiest way to demo it, and the most honest interface for "I need to look up one shipment." The CS person can run `pf-lookup PF-1003` from their terminal.

4. **Type hints.** They are not just for IDE autocomplete. They are how you tell future-you (and the customer) what each function expects. AI tools especially benefit from type hints, because the IDE can catch the bug where you pass a string where you meant a list of strings.

That is the whole lesson. Everything else is mechanics.

## 🛠️ Build It (20 min)

### Step 1 — Create the project layout

From the repo root:

```bash
cd course/ai-fde/phase-1-foundations
python3 -m venv .venv
source .venv/bin/activate     # macOS / Linux
# .venv\Scripts\activate    # Windows PowerShell
python3 -m pip install --upgrade pip
python3 -m pip install python-dotenv
```

You now have a `.venv/` directory. **It is not in source control.** Make sure your `.gitignore` has it (lesson 02 covers this).

### Step 2 — Create `.env.example` and `.env`

`.env.example` is committed to source. It shows what variables the tool expects, with no real values:

```bash
# PacificFreight — environment variables
# Copy this file to .env and fill in the real values. .env is gitignored.

# The internal tracker. In Phase 1 this is a local JSON file.
PF_TRACKER_PATH=./shared/shipments.json

# The default CS rep name that signs drafts.
PF_REP_NAME=Linh

# LLM provider — leave blank to use the mock backend.
PF_LLM_PROVIDER=
PF_OPENAI_API_KEY=
PF_ANTHROPIC_API_KEY=
```

Copy it to `.env`:

```bash
cp .env.example .env
# Leave PF_LLM_PROVIDER blank for now — we'll use the mock.
```

### Step 3 — Write the CLI

Open `technical/01-python-tooling.py`. The full file is below. It is 50 lines, no AI yet, just Python + JSON + argparse.

```python
"""
Lesson 01 — pf-lookup: a tiny CLI that reads shipments.json.

What you should be able to explain to a client after this lesson:
- What a virtual environment is, and why we use one.
- Why we keep secrets in .env, not in source.
- Why we use argparse (so the customer can run the tool themselves).

How to run:
    python3 technical/01-python-tooling.py PF-1003
    python3 technical/01-python-tooling.py --help
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env into os.environ (does NOT overwrite existing vars)


@dataclass(frozen=True)
class Shipment:
    id: str
    customer_name: str
    status: str
    last_event: str
    last_event_at: str
    next_action_required: str | None = None


def load_shipment(tracker_path: Path, shipment_id: str) -> Shipment | None:
    """Look up a shipment by ID. Returns None if not found."""
    with tracker_path.open() as fh:
        data = json.load(fh)
    for s in data["shipments"]:
        if s["id"].upper() == shipment_id.upper().strip():
            return Shipment(
                id=s["id"],
                customer_name=s["customer_name"],
                status=s["status"],
                last_event=s["last_event"],
                last_event_at=s["last_event_at"],
                next_action_required=s.get("next_action_required"),
            )
    return None


def format_summary(s: Shipment) -> str:
    """Print a one-screen summary a human can read in 5 seconds."""
    lines = [
        f"Shipment {s.id}  (customer: {s.customer_name})",
        f"Status: {s.status}",
        f"Last event ({s.last_event_at}): {s.last_event}",
    ]
    if s.next_action_required:
        lines.append(f"Action: {s.next_action_required}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Look up a PacificFreight shipment by ID.",
    )
    parser.add_argument("shipment_id", help="e.g. PF-1003")
    parser.add_argument(
        "--tracker",
        default=os.getenv("PF_TRACKER_PATH", "./shared/shipments.json"),
        help="Path to shipments.json",
    )
    args = parser.parse_args()

    tracker_path = Path(args.tracker)
    if not tracker_path.exists():
        print(f"ERROR: tracker not found at {tracker_path}", file=sys.stderr)
        return 1

    shipment = load_shipment(tracker_path, args.shipment_id)
    if shipment is None:
        print(f"ERROR: no shipment with ID {args.shipment_id!r}", file=sys.stderr)
        return 2

    print(format_summary(shipment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 4 — Run it

```bash
python3 technical/01-python-tooling.py PF-1003
python3 technical/01-python-tooling.py pf-1003   # case-insensitive
python3 technical/01-python-tooling.py --help
python3 technical/01-python-tooling.py PF-9999   # exits 2
```

Notice the exit codes: `0` for success, `1` for missing file, `2` for missing shipment. The CS person will be running this in a script later, so honest exit codes matter.

### Step 5 — Make it pretty

Add `--json` flag to output machine-readable JSON. About 5 more lines:

```python
parser.add_argument("--json", action="store_true", help="Output JSON instead of formatted text")
```

And:

```python
if args.json:
    print(json.dumps(shipment.__dict__, indent=2, ensure_ascii=False))
else:
    print(format_summary(shipment))
```

Now `pf-lookup PF-1003 --json` works, and your future AI tool can pipe it.

## 🏛️ FDE Lens — the one question to ask the client

> *"When you and your team run this tool, are you comfortable with the terminal — or do you need a web UI before you will use it?"*

The answer determines the rest of Phase 2. Most 12-person SMBs say *"yes I can use the terminal"*. Some say *"absolutely not."* You don't want to find out 6 weeks in.

## 🌙 Reflect

Write 3-5 sentences in your own notes:

1. Why is `.env` in `.gitignore` and not committed?
2. What does `argparse` buy you that hard-coded `sys.argv[1]` doesn't?
3. What's the difference between exit code 1 and exit code 2 in `pf-lookup`?
4. The `next_action_required` field is `Optional[str]`. When is it `None`? Why use `| None` instead of leaving the field out?

**What's next** — Lesson 02 puts this CLI into git, properly, with a `.gitignore` that protects secrets. You will also learn the "branch per change" workflow that FDEs use to ship without breaking the customer's day.
