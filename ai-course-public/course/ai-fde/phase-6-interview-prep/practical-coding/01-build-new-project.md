# Practical Coding Sub-Lesson 1 — Build a New Project (greenfield, 90 min, AI-assisted)

> **This is the most common practical-coding sub-round.** Pioneered at Meta, Anthropic, and OpenAI in 2024-2025. The format: 90 minutes, a realistic prompt, "build a small CLI tool that does X." You can use an AI assistant. **The signal: a candidate who uses the AI assistant well — to draft the boilerplate, to verify the test, to navigate the codebase — is showing they can ship in 2026.**

---

## Why this sub-round is the FDE signal

The 4 things the interviewer is testing:

1. **Can you scope?** 90 minutes is short. The candidate who tries to build 5 features fails. The candidate who builds 1 feature well wins.
2. **Can you use the AI assistant well?** The AI is a typing accelerator, not a thinking partner. The candidate who uses the AI to draft the boilerplate and verify the test is showing they can ship in 2026.
3. **Can you write tests?** The eval set is the spec. The candidate who writes 5-10 tests in the first 20 minutes is signaling they understand the contract.
4. **Can you ship the 5 deliverables?** Code + tests + README + cost model + runbook. The candidate who ships 3 of 5 fails.

**The FDE pattern:** spec first, build second, evaluate third, hand off fourth. Same as the take-home, compressed to 90 minutes.

---

## The prompt template (the most common format)

> "Build a small CLI tool that does X. You have 90 minutes. You can use any tools you want, including an AI assistant."

**The X is one of:**

- **CLI tool:** parse a CSV, transform JSON, deduplicate a list, etc.
- **Web scraper:** fetch a URL, extract the data, save to a file.
- **Mini API:** 3-5 endpoints, with tests, with a README.
- **Data pipeline:** read from one source, transform, write to another.

**The 5 deliverables (always):**

1. **The code** (1-3 files, ~200-500 lines).
2. **The tests** (5-10 tests, including the spec).
3. **The README** (1 page: how to run, the design decisions, the tradeoffs).
4. **The cost model** (if applicable: $/month for the use case).
5. **The runbook** (1 paragraph: how to operate the tool).

---

## The 3-phase plan (90 minutes)

### Phase 1: Spec + Eval Set (10 minutes)

**Goal:** lock the spec. The eval set is the contract.

**The 4 sub-tasks:**

1. **Read the prompt carefully.** Note: (a) the input format, (b) the output format, (c) the time budget, (d) the deliverables.
2. **Pick the "wow" moment.** The one thing that, if it works, makes the customer say "I need this." Resist the urge to ship 5 things.
3. **Write 5-10 tests.** The tests are the spec. The tests are the eval set. The tests are the contract.
4. **Sketch the architecture.** 1-page diagram: input → processing → output. Don't write code yet.

**The 3 deliverables for Phase 1:**

- A 1-line spec ("The tool reads a CSV, dedupes by column X, and writes a JSON file.")
- A 5-10 test file (`test_X.py` with the 5-10 test cases)
- A 1-page architecture diagram (could be a comment in the code)

### Phase 2: Implementation (60 minutes)

**Goal:** ship the "wow" moment with the 5 deliverables.

**The 4 sub-tasks:**

1. **Set up the repo.** `git init`, `README.md`, `requirements.txt`, `.env.example`, `Makefile`.
2. **Write the code.** 1-3 files, ~200-500 lines. Use the AI assistant to draft the boilerplate, but verify every line.
3. **Run the tests.** `pytest` should pass on the first run. If it doesn't, debug.
4. **Add the cost model + runbook.** 1 paragraph each. Total: 2 paragraphs.

**The 5 deliverables for Phase 2:**

- `README.md` (1 page: how to run, the design decisions, the tradeoffs)
- `requirements.txt` (pinned dependencies)
- `Makefile` (with `make test`, `make run`, `make clean`)
- `COST_MODEL.md` (1 paragraph: $/month for the use case)
- `RUNBOOK.md` (1 paragraph: how to operate the tool)

### Phase 3: Polish + Tests (20 minutes)

**Goal:** make the artifact operable by someone who isn't you.

**The 4 sub-tasks:**

1. **Add edge cases.** Empty input, single element, all duplicates, negative numbers. The edge cases are the signal.
2. **Run the test suite one more time.** `pytest` should pass on the first run. If it doesn't, debug.
3. **Update the README.** The README should be readable in 60 seconds.
4. **Final review.** Walk through the code one more time. Cite the AI in the README.

**The 3 anti-patterns to avoid in Phase 3:**

1. **Skipping the edge cases.** The edge cases are the signal.
2. **Skipping the README + handoff note.** The handoff is the FDE signal.
3. **Going over time.** 90 minutes is 90 minutes. Practice with a timer.

---

## The worked example: "Build a CLI tool that deduplicates a CSV by email"

### Phase 1: Spec + Eval Set (10 minutes)

**The spec:**

> "The tool reads a CSV from stdin, deduplicates rows by the `email` column (case-insensitive), and writes the deduplicated CSV to stdout. The tool handles malformed rows by logging them to stderr and skipping them."

**The 5-10 test cases (`test_dedup.py`):**

```python
def test_basic_dedup():
    # 3 rows, 2 unique emails
    # Expected: 2 rows in output

def test_case_insensitive():
    # "Alice@example.com" and "alice@example.com"
    # Expected: 1 row in output

def test_empty_input():
    # Empty CSV
    # Expected: empty output

def test_malformed_rows():
    # 1 valid row, 1 row missing email column
    # Expected: 1 row in output, 1 row logged to stderr

def test_whitespace_in_email():
    # " alice@example.com " and "alice@example.com"
    # Expected: 1 row in output

def test_unicode_email():
    # "alice@example.com" and "ALICE@EXAMPLE.COM"
    # Expected: 1 row in output

def test_duplicate_preserves_first():
    # 3 rows with same email, different names
    # Expected: 1 row (the first one) in output

def test_large_input():
    # 100K rows, 50% duplicates
    # Expected: 50K rows in output, completes in < 5 seconds
```

### Phase 2: Implementation (60 minutes)

**The code (`dedup.py`):**

```python
#!/usr/bin/env python3
"""CSV deduplication CLI tool."""
import csv
import sys
import logging

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def normalize_email(email: str) -> str:
    """Normalize email for comparison: lowercase, strip whitespace."""
    return email.strip().lower()

def dedup_csv(input_stream, output_stream):
    """Deduplicate CSV by email column. Malformed rows are logged and skipped."""
    reader = csv.DictReader(input_stream)
    writer = None
    seen = set()
    stats = {"input": 0, "output": 0, "skipped": 0, "duplicates": 0}

    for row in reader:
        stats["input"] += 1
        email = row.get("email", "").strip()
        if not email:
            logging.warning(f"Skipping row {stats['input']}: missing email")
            stats["skipped"] += 1
            continue
        normalized = normalize_email(email)
        if normalized in seen:
            stats["duplicates"] += 1
            continue
        seen.add(normalized)
        if writer is None:
            writer = csv.DictWriter(output_stream, fieldnames=row.keys())
            writer.writeheader()
        writer.writerow(row)
        stats["output"] += 1

    logging.info(f"Stats: {stats}")
    return stats

if __name__ == "__main__":
    dedup_csv(sys.stdin, sys.stdout)
```

**The README (`README.md`):**

```markdown
# CSV Dedup CLI

Deduplicates a CSV by the `email` column (case-insensitive).

## Usage
    cat input.csv | python dedup.py > output.csv

## Design decisions
- Email is normalized to lowercase + stripped of whitespace for comparison.
- First occurrence of each email is preserved.
- Malformed rows (missing email) are logged to stderr and skipped.
- Streaming: handles 100K+ rows in < 5 seconds with constant memory.

## Tests
    pytest test_dedup.py

## Cost model
- Memory: O(unique emails), bounded by input size.
- CPU: O(n) where n = number of rows.
- For 1M rows: ~5 seconds, ~50MB memory.

## Runbook
- If the tool hangs, check for malformed UTF-8 in the input.
- If the tool crashes, check the Python version (3.8+).
- This tool was drafted with Claude; I verified every line and added 8 tests.
```

**The Makefile:**

```makefile
.PHONY: test run clean

test:
	pytest test_dedup.py -v

run:
	@cat sample.csv | python dedup.py

clean:
	find . -type f -name "*.pyc" -delete
	rm -rf __pycache__
```

### Phase 3: Polish + Tests (20 minutes)

**The 3 things to add:**

1. **Edge case: handle BOM (byte-order mark) in the input.** Add `encoding="utf-8-sig"` to the `csv.DictReader`.
2. **Edge case: handle empty email column.** Already handled.
3. **Edge case: handle CSV with no header.** Add a check in the code.

**The final review:**

- Run `pytest test_dedup.py -v` → 8/8 passing.
- Run `cat sample.csv | python dedup.py > output.csv` → works.
- Read the README out loud → 60 seconds.

---

## The 5 AI assistant etiquette rules

1. **Tell the AI what you're building.** "I'm building a CLI tool that deduplicates a CSV by email. Here's the spec." The AI needs context.
2. **Verify every line of AI-generated code.** Read it. Test it. Don't trust the AI.
3. **Use the AI to explore, not to think.** "Where is the email normalization in the code?" is exploration. "What should the email normalization look like?" is thinking. The thinking is your job.
4. **Cite the AI in the README.** "This code was drafted with Claude; I verified every line and added 8 tests." The citation is the signal.
5. **Know when to stop using the AI.** If the AI is hallucinating or going in circles, stop. Read the code yourself.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How did you use the AI assistant?" | "I used it as a typing accelerator for the boilerplate. I drafted the spec, the AI drafted the code, I verified every line. I added 8 tests to verify the AI's code." |
| 2. "What would you do without an AI assistant?" | "I'd write the same code, just slower. The spec is the same; the tests are the same. The AI saves typing time; it doesn't change the design." |
| 3. "What's the bug you fixed, and how would you prevent it?" | "The bug was a case-sensitivity issue in the email comparison. The fix was to normalize the email to lowercase before comparison. The prevention is the test case `test_case_insensitive`." |

---

## The 5 anti-patterns

1. **Skipping the spec.** "I'll just start coding" is a junior answer. The spec is the eval set; the eval set is the contract.
2. **Trusting the AI's code without verification.** The AI generates code that looks right. The bug is in the line you didn't read.
3. **Spending 80 minutes on the code, 10 on the tests.** The tests are the proof. Without them, the code is unverified.
4. **Skipping the README + handoff note.** The handoff is the FDE signal. Without it, the code is a prototype.
5. **Going over time.** 90 minutes is 90 minutes. Practice with a timer. Going over is a red flag.

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../take-home/01-prototype.md` | The 4-hour build plan (the same pattern, compressed) |
| `../swe-coding/README.md` | The 8 SWE patterns (the foundation for the code) |
| `../behavioral/README.md` | The STAR format (for the wrap-up) |

---

## The thesis

**Build a new project is the most common practical-coding sub-round.** The candidate who uses the AI assistant well — to draft the boilerplate, to verify the test, to navigate the codebase — is showing they can ship in 2026. The candidate who tries to build 5 features in 90 minutes fails.

**The 3-phase plan (10 min spec + 60 min implementation + 20 min polish) is the muscle memory.** The 5 deliverables (code + tests + README + cost model + runbook) are the FDE signal. The 5 AI assistant etiquette rules are the meta-signal.

**General prep gets you past the resume screen. Practical-coding prep gets you past the centerpiece round at Meta, Anthropic, and OpenAI.**