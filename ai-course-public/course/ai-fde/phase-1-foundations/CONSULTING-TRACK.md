# Consulting Track — AI FDE Phase 1

> **You finish this track and you have a 1-pager + a solution outline you can hand to a client.**
> Five lessons, ~3 hours total. No code — only the documents that make the code worth shipping.

This track teaches the **client-engagement craft** of an AI FDE: how to walk into a customer, ask the right questions, frame a use case that is testable, and leave with a written scope everyone agrees on.

---

## Lesson map

| # | Lesson | What you produce | Time |
|---|---|---|---|
| 01 | [Understanding the problem](./consulting/01-understanding-the-problem.md) | A stakeholder map + a discovery question list | 25 min |
| 02 | [Asking better questions](./consulting/02-asking-better-questions.md) | The 5-question framing framework, with 2 worked examples | 30 min |
| 03 | [Prompting patterns & APIs](./consulting/03-prompting-patterns.md) | A prompt-pattern cheatsheet + 3 prompt variants for the same task | 30 min |
| 04 | [Framing an AI use case](./consulting/04-framing-an-ai-use-case.md) | **The 1-pager** — the "testable use case" template, filled in for PacificFreight | 40 min |
| 05 | [Solution outline](./consulting/05-solution-outline.md) | **The solution outline** — components, data flow, cost, risks, next steps | 40 min |

After lesson 05, you have the **clear problem statement** + the **initial solution outline** — the other half of Phase 1's deliverable.

---

## The consulting skill in one line

> **An FDE's job is to write the document the client didn't know they needed, then build the smallest thing that proves it.**

The consulting track is the document half. The technical track is the code half. Phase 1 is done when you have both, for the same customer, in the same week.

---

## The 1-pager template (the deliverable of lesson 04)

A good 1-pager fits on **one printed page**. It has these sections, in this order:

1. **The user** — who is affected, how often, in what context.
2. **The job** — what they are trying to do, in their own words.
3. **The pain** — measured in time, money, errors, or stress.
4. **The AI-shaped hypothesis** — what an AI system could do, in one sentence.
5. **The success metric** — how you will know it worked, with a number.
6. **The cost ceiling** — what they would pay (per month, per use, or per saved minute).
7. **The risks** — the 2-3 things most likely to fail or embarrass the client.
8. **The test plan** — how you will know in 1 week whether to keep going.

If you can't fill all 8, you don't have a use case — you have a vibe. The 1-pager is what turns the vibe into a commitment.

The full template + a filled-in PacificFreight example is in [`04-framing-an-ai-use-case.md`](./consulting/04-framing-an-ai-use-case.md).

---

## How the two tracks meet

You will work the same scenario through both tracks:

| Consulting artifact | Technical artifact |
|---|---|
| Discovery questions (lesson 01) | Informs the **CLI's inputs** (lesson 04) |
| Prompt patterns (lesson 03) | Informs the **drafting prompt** in the CLI |
| 1-pager (lesson 04) | The **README of the first working tool** |
| Solution outline (lesson 05) | The **ARCHITECTURE sketch of the system** |

When you finish Phase 1, hand the consulting artifacts to the client and demo the technical artifacts in the same meeting. That is the FDE loop.

---

## What's next

- The **Technical Track** — the other half. Build the tool those documents justify.
- **`course/projects/ai-engineer-capstone-guide.md`** — the larger engagement model (5-8 weeks, multi-stakeholder).
- **`course/workbooks/`** — paired exercises for the AI engineer codebook, useful when you need a reference mid-engagement.
