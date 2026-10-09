# Lesson 02 — Git for AI Work

> **The minimum git workflow you need to ship an AI tool without leaking a customer's API key.** 20 minutes.

By the end of this lesson you have:

- A fresh git repo in `course/ai-fde/phase-1-foundations/`
- A `.gitignore` that protects `.env`, `.venv`, and all the other things an FDE should never commit
- A **branch per change** workflow (so the customer always has a working main)
- A "commit message that explains the why" template (so 6 months from now you can read it)
- A **PR description** template (so the customer can review without a meeting)

Git is the boring skill that lets you ship a v0.1 on Monday and a v0.2 on Friday without the customer ever seeing a broken state.

---

## 🎯 You will build

A scripted mini workflow that:

1. Initializes git in this lesson's folder
2. Adds a proper `.gitignore`
3. Makes the first commit ("scaffold: project skeleton")
4. Creates a feature branch (`feat/lookup-cli`)
5. Adds lesson 01's `pf-lookup.py` on that branch
6. Makes a second commit ("feat: add pf-lookup CLI for one-shot shipment lookups")
7. Shows you the diff you'd open as a PR

## 🧠 Concept (5 min)

The four things an FDE needs from git, and nothing more:

1. **A `.gitignore` that protects secrets.** This is the single most important file. If `.env` is in `.gitignore` you cannot accidentally commit an API key. If it is not, one typo and the customer's OpenAI key is on GitHub.

2. **A clean main branch.** Main is always the thing the customer can run. You do your work on a branch. You merge back when the customer has approved the change. This is not ceremony — it is how you can demo on Tuesday without your half-done Wednesday work breaking the demo.

3. **Commit messages that explain the *why*.** `"fix stuff"` is useless in 6 months. `"fix: stop crashing on missing shipment_id — return None instead" tells you the bug, the fix, and the new contract. The customer will read these too.

4. **PR descriptions the customer can read.** Your customer is not a developer. They will look at the PR description in the GitHub UI, not the diff. Write it for them.

That is it. You do not need rebase, you do not need interactive staging, you do not need submodules. Those are for engineers with bigger problems than you.

## 🛠️ Build It (15 min)

### Step 1 — Initialize the repo

From this folder (`course/ai-fde/phase-1-foundations/`):

```bash
git init
git config user.email "you@example.com"     # your real email
git config user.name  "Your Name"
```

> **FDE tip:** if you are working for a real customer, use the email they issued you, or a personal one that you can hand off cleanly when the engagement ends. Do not use your previous employer's email.

### Step 2 — Create `.gitignore`

```gitignore
# FDE Phase 1 .gitignore
# Anything customer-specific or secret goes here. NEVER commit these.

# Environment
.env
.env.*
!.env.example
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/

# Tool-specific caches
.mypy_cache/
.ruff_cache/
.idea/
.vscode/

# Local outputs (CLI demos, generated reports)
*.log
out/
tmp/

# The customer data we use for testing — never commit real customer data.
# (Our shared/shipments.json is a mock, so it's fine to commit. Real data is NOT.)
*-prod.json
```

The pattern `!.env.example` is important — it *excludes* `.env*` (so `.env` is ignored) but *re-includes* `.env.example` (so the template is committed). This is the most common gitignore mistake.

### Step 3 — First commit: scaffold

```bash
git add .gitignore .env.example
git commit -m "chore: scaffold repo with .gitignore and .env template

Why: protects the customer from a leaked API key on day one.
What: standard Python + secrets gitignore, plus a .env.example
that documents every variable the tool expects."
```

Notice the format: `<type>: <one-line summary>` followed by a blank line and a `Why` / `What`. That is the format you will use for every commit in Phase 1.

Conventional commit types you will use:
- `feat:` — a new feature
- `fix:` — a bug fix
- `chore:` — repo maintenance, no behavior change
- `docs:` — documentation only
- `refactor:` — code change that doesn't add a feature or fix a bug

### Step 4 — Branch per change

```bash
git checkout -b feat/lookup-cli
```

The branch name format is `<type>/<short-kebab-summary>`. Now your work is isolated from `main`. The customer can pull `main` and it still works.

### Step 5 — Add lesson 01's CLI on the branch

```bash
cp ../practice/capstone-starters/01-ai-doc-qa/app.py /tmp/ignore  # not real, just demonstrating
# Actually:
# We added lesson 01 in lesson 01, so it's already on disk.
git add technical/01-python-tooling.py
git status
```

The `git status` should show only `technical/01-python-tooling.py` as a new file.

### Step 6 — Second commit: the CLI

```bash
git commit -m "feat: add pf-lookup CLI for one-shot shipment lookups

Why: CS team needs a fast terminal way to look up a single shipment
when the email only mentions one ID. The web tracker is too slow
for this (3-4 clicks, 20 seconds) and CS staff already live in the
terminal.

What: 50-line CLI that reads shipments.json, supports --json output,
returns honest exit codes (0=ok, 1=missing file, 2=missing shipment).
No AI yet — that lands in lesson 04.

Test: python3 technical/01-python-tooling.py PF-1003 prints the
held_customs status; --help lists both flags."
```

That commit message is what makes the customer trust you. It says *what*, *why*, and *how to test* in 6 lines.

### Step 7 — Open a PR (locally, no GitHub needed)

In a real engagement you would `git push` and open a PR on GitHub. In Phase 1, simulate it with a text file:

```bash
mkdir -p .pr
cat > .pr/feat-lookup-cli.md <<'EOF'
# feat: pf-lookup CLI

## What
Adds a 50-line Python CLI that looks up a single shipment by ID
and prints a one-screen summary (or JSON, with --json).

## Why
CS team is currently 4-7 minutes per "where is my parcel?" email.
The first step of that is looking the shipment up. Terminal lookup
takes 2 seconds and lets us automate the rest in lesson 04.

## How to test
    python3 technical/01-python-tooling.py PF-1003
    python3 technical/01-python-tooling.py PF-1003 --json
    python3 technical/01-python-tooling.py PF-9999   # exit 2

## Risk
Low. Read-only against a JSON file. No network. No API key.

## What I am NOT doing
- No AI yet (lesson 04).
- No web UI (Phase 2 if you want one).
- No integration with the real PHP tracker (separate engagement).
EOF
git add .pr
git commit -m "docs: add PR description for feat/lookup-cli"
```

When you eventually push to GitHub, this becomes the PR body. The customer reads it in 30 seconds and knows exactly what you did and what to test.

### Step 8 — Run the full scripted workflow

For repeatable, demo-able execution, the whole lesson is in `technical/02-git-for-ai-work.sh`. Read it once, then run it on a fresh folder to see the full sequence in 10 seconds:

```bash
bash technical/02-git-for-ai-work.sh
```

The script is idempotent — if you run it in a folder that already has a `.git/`, it skips the init. So you can demo it to the customer.

## 🏛️ FDE Lens — the one question to ask the client

> *"Where do you want me to push the code — a GitHub repo, a GitLab, your own internal git server, or just a shared folder?"*

Their answer determines:
- whether you need to teach them the PR review UI
- whether you can use GitHub Actions / webhooks (only GitHub/GitLab)
- whether you can sign commits with GPG (some regulated customers require it)

## 🌙 Reflect

Write 3-5 sentences:

1. Why is `.env` in `.gitignore` but `.env.example` is NOT?
2. What does `git checkout -b feat/lookup-cli` do, and why is the branch name kebab-cased?
3. The PR description has a "What I am NOT doing" section. Why does that matter?
4. When would you use `git commit --amend`? When would you NOT?

**What's next** — Lesson 03 swaps the hard-coded JSON lookup for a real LLM call. You will write a unified client that supports OpenAI, Anthropic, and a deterministic mock, so the tool can demo today and ship with a real model next week.
