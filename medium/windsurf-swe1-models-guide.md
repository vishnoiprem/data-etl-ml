# I Switched to Windsurf's SWE-1 Models for a Week. Here's What Actually Changed.

*Windsurf ships its own AI models built specifically for coding. I tested them against GPT-4o and Claude on real tasks. The results surprised me.*

---

I've been using AI coding assistants since GitHub Copilot launched. Cursor for a year. Then I switched to Windsurf three months ago because a coworker wouldn't shut up about it.

For the first two months, I used Claude Sonnet for everything inside Windsurf. It worked fine. Then I actually read the docs and realized Windsurf has its own model family — SWE-1 — that I'd been completely ignoring.

So I ran a week-long experiment. Every task I'd normally throw at Claude, I tried with SWE-1 first. Here's what happened.

---

## What SWE-1 actually is

Windsurf built three models from scratch, trained specifically on software engineering workflows. Not just code — the *process* of writing code. Editing, debugging, reading terminal output, iterating. They call this "flow awareness."

The three models:

**SWE-1** — The heavy one. Multi-file refactoring, architecture, complex planning. Costs 1 credit per prompt.

**SWE-1-lite** — The daily driver. Code explanation, unit tests, quick refactors. Free.

**SWE-1-mini** — The autocomplete engine. Powers the Tab key suggestions. Free.

The pricing matters. SWE-1-lite being free means you can use it hundreds of times a day without thinking about cost. That changes behavior — you stop rationing your AI usage and start treating it like a conversation.

---

## Day 1: Building an API from scratch

My task: build a Flask API for time tracking. CRUD endpoints, PostgreSQL, basic auth.

I opened Cascade (Windsurf's chat panel) and typed:

```
Build a RESTful Flask API with endpoints to create, fetch, 
and delete time entries. Each entry has user_id, task_name, 
duration_minutes. Use SQLAlchemy with PostgreSQL. Add JWT auth.
```

With **SWE-1-lite** (free), I got a working single-file implementation. Correct routes, proper SQLAlchemy models, JWT decorator. Took 8 seconds. Missed some edge cases but the structure was solid.

Same prompt with **SWE-1** (1 credit), and the difference was obvious. It created four files: `app.py`, `models.py`, `auth.py`, `config.py`. It added error handling, input validation with marshmallow, and proper HTTP status codes. It also created a `.env.example` file without me asking.

SWE-1 didn't just generate code. It *planned* a project structure.

**My rule after Day 1:** SWE-1-lite for single-file tasks. SWE-1 for anything that touches multiple files.

---

## Day 2: Debugging something weird

My FastAPI app was returning 422 errors on a POST endpoint that worked yesterday. I highlighted the route and the Pydantic model, then asked Cascade:

```
Why is this returning 422? It worked before I added the 
optional fields.
```

SWE-1-lite nailed it in 3 seconds. The issue was a Pydantic v2 breaking change — `Optional[str]` no longer defaults to `None`, you need `Optional[str] = None` explicitly. It showed me the fix and explained the v1→v2 migration difference.

I didn't need a heavy model for this. SWE-1-lite's speed made it feel like asking a coworker sitting next to me. No loading spinner, no waiting. That speed matters more than people think.

---

## Day 3: Refactoring a mess

I had a 400-line React component that did everything — fetching, state management, rendering, event handlers. Classic God Component. I asked SWE-1:

```
Refactor this into smaller components. Extract the data 
fetching into a custom hook. Keep the same behavior.
```

It broke the file into five pieces: `useTimeEntries.ts` (custom hook), `TimeEntryList.tsx`, `TimeEntryForm.tsx`, `TimeEntryItem.tsx`, and the cleaned-up parent. It moved the shared types into a `types.ts` file. Every import was correct.

I tried the same task with Claude 4 Sonnet. It also did a good job — arguably the component naming was slightly better — but it missed one import and put a type definition in the wrong file. SWE-1 got the *project structure* right because it could see my full codebase, not just the file I pasted.

This is what Windsurf means by "flow awareness." The model sees your terminal, your recent edits, your file tree. That context makes multi-file refactoring dramatically more reliable.

---

## Day 4: Writing tests

This is where SWE-1-lite earned its keep. I selected a utility function and typed:

```
Write tests for this. Use pytest. Cover edge cases.
```

12 seconds later: 8 test cases including null input, empty string, boundary values, and a Unicode edge case I wouldn't have thought of. All passing. Free.

I ran this pattern probably 15 times that day. Select function → "write tests" → paste into test file → run. Because SWE-1-lite is free, I didn't think twice about using it for every function. With a paid model I would have batched them or skipped the less critical ones.

Free changes your habits.

---

## Day 5: The task where I switched models

I needed to write the README for an open-source project. Installation, usage examples, API reference, contributing guidelines.

I started with SWE-1-lite. The output was technically accurate but read like documentation written by someone who'd never read a good README. Dry. Bulletpoint-heavy. No personality.

I switched to Claude 4 Sonnet:

```
Write a README for Chrono-Logger, a TypeScript library for 
performance timing. Make it welcoming and professional. Include 
Installation, Quick Start with a code example, API Reference, 
and Contributing. Keep it concise.
```

Much better. The opening paragraph had a clear value proposition. The code examples were practical. The tone was inviting. Claude is just better at prose.

**My rule after Day 5:** SWE-1 for code. Claude or GPT for writing that humans read.

---

## The model selection cheat sheet

After a week, my decision process became automatic:

| Task | Model | Why |
|---|---|---|
| Typing / autocomplete | SWE-1-mini (automatic) | It's the Tab key. Fast. |
| "Explain this code" | SWE-1-lite (free) | Fast, accurate, free |
| "Write tests for this" | SWE-1-lite (free) | Does it well, use it 20x/day |
| Quick bug fix | SWE-1-lite (free) | 3-second answers |
| Multi-file refactor | SWE-1 (1 credit) | Understands project structure |
| New feature scaffold | SWE-1 (1 credit) | Plans before generating |
| README / docs | Claude 4 Sonnet (2 credits) | Better prose |
| "Summarize this research paper" | GPT-4o (1 credit) | Better at general text |

The pattern: **free model by default, pay only when the task demands it.**

---

## What "flow awareness" actually means in practice

Windsurf talks a lot about flow awareness. Here's what it means concretely.

When I ask SWE-1 to fix a bug, it doesn't just see the file I'm looking at. It sees:

- Which files I've edited in the last 10 minutes
- What's in my terminal (including error output)
- My cursor position
- My recent Cascade conversation

So when I get a test failure and type "fix this," SWE-1 already knows which test failed, which file the error points to, and what I changed recently. It connects the dots without me having to explain the full context.

Other models inside Windsurf get some of this context too. But SWE-1 was trained on this exact loop — edit code, run test, read error, fix code — so it uses the context better. The difference is subtle but it compounds over a full day.

---

## The credit math

Windsurf's pricing is straightforward:

- **Free plan:** Limited monthly credits
- **Pro plan:** Solid monthly credit allocation + unlimited free model usage

The key insight: SWE-1-lite and SWE-1-mini are **free on every plan.** They handle 80% of my daily tasks. I only burn credits on SWE-1 for complex work (maybe 10–15 prompts/day) and Claude/GPT for specialized tasks (2–3 prompts/day).

If you have your own Anthropic API key, you can use BYOK (Bring Your Own Key) for Claude models — zero Windsurf credits charged. This doesn't work for OpenAI or Gemini models though.

---

## Honest take: where SWE-1 falls short

It's not perfect.

**Long prose:** As I said, writing that humans read (docs, READMEs, commit messages) is better with Claude or GPT. SWE-1 writes like an engineer, which is great for code comments but not for user-facing text.

**Niche frameworks:** If you're using something obscure, the generalist models sometimes know more because they were trained on a wider variety of text. SWE-1 is deep on mainstream development patterns.

**Creative solutions:** For "I have no idea how to approach this problem" moments, I sometimes get more creative suggestions from Claude. SWE-1 tends to give you the conventional solution, which is usually what you want — but not always.

---

## The bottom line

Before this experiment I was paying for every AI interaction inside Windsurf. Now 80% of my usage is free (SWE-1-lite), and the paid prompts I do use are more targeted and effective because I'm picking the right model for each task.

The SWE-1 family isn't better than Claude or GPT at everything. It's better at the specific thing I do all day: writing, debugging, and refactoring code inside an editor. That specialization — plus being free — makes it the obvious default.

Stop using a $0.02/prompt model to explain a regex. Use SWE-1-lite. Save your credits for when you actually need the heavy reasoning.

That's the whole strategy. It's not complicated. It just took me two months to figure out.

---

*Tags: Windsurf · AI Coding · SWE-1 · Developer Tools · Productivity*
