---
name: SignalScribe article project scope
description: Scope, topic, platform, disclosure stance, and deliverable definition for the "how to pick the best article/tool/paper" article project
type: project
---

The SignalScribe project in `agentic-ai/20-ai-find-best-article/` produces one long-form article on **how to evaluate and select the best article, tool, paper, model, or prompt for a given job**, scoped to AI, data engineering, ML, agentic systems, and emerging technology.

**Platform:** LinkedIn / Medium. Newsletter-style long form, 1,000–1,800 words, narrative-forward with a strong hook in the first two lines. Fewer inline code blocks than a dev blog; heavier on takeaway and decision rules. SEO-conscious title.

**Core thesis of the article:** "Best" is not a property of the artifact — it is a property of a specific job, under specific constraints, judged by someone who can detect the failures that matter. Selection is a procedure you run, not a ranking you read.

**Disclosure stance:** AI-assisted. The pipeline produces drafts and reviews only; it never publishes. The final article is routed to a human, who must replace every `[AUTHOR EXPERIENCE: ...]` placeholder with a real firsthand account and sign off on the factual claims before it can go out.

**Deliverable scope:** research + 100 distinct drafts + 100 structured review passes, plus a persistent memory system. Not a blog post, not a tutorial series, not a code project.

**Why:** The user chose this depth deliberately — the article is a credibility artifact for a technical audience, so the evidence trail and the review trail are the point, not a side effect. A thin review trail would make the piece undefendable.

**How to apply:** When resuming work in this directory, read `rubric.md`, `voice-guide.md`, `outline.md`, `article-template.md`, `research/notes.md`, and `sources.md` before touching any draft or review. Treat `sources.md` as the closed vocabulary of citable facts — a claim that is not in `research/notes.md` does not belong in a draft. Never mark the work as publishable; the human sign-off gate in `README.md` is binding.
