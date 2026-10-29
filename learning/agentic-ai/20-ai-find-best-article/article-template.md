# Article Template

Copy this structure. Every draft in this project uses it, varying content and ordering of sections but not the front-matter fields or the presence of the disclosure and source list.

---

```markdown
---
title: "<SEO-conscious, specific title under ~70 characters>"
subtitle: "<A concrete promise, not a platitude>"
tags:
  - ai-evaluation
  - llm
  - <3-5 more specific tags, at least one long-tail phrase>
platform: linkedin
medium_publication: signal-scribe
target_length: 1200-1500
word_count: <actual>
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: <0-100>
hard_fail: false
distinctness_angle: "<one line naming this draft's organizing device, angle, and example set>"
sources_count: <n>
author_experience_placeholders: <n>
---

<!-- BODY OPENS HERE. One sentence per line for mobile scanning. -->

<Hook: two lines. A concrete tension, number, or challenge. No definitions.>

<Thesis: one falsifiable sentence, within the first 150 words.>

## <First section heading: specific, 2-6 words, sentence case>

<Paragraph: one idea, 1-3 sentences.>

<Second paragraph.>

## <Second section heading>

<The evidence. Inline citations to sources. Exact numbers, attributed with context.>

<Paragraph.>

## <Decision framework section — the heart>

<Five or more mechanical decision rules. Numbered, or bulleted, or in the draft's own shape.>

<Worked example one: concrete, specific, drawn from the sources.>

<Worked example two: different context, different role.>

## <Limitations section>

<Plain statements: no validated algorithm exists; numbers are setup-specific; preprint vs peer-reviewed split; what this cannot settle.>

## <Next steps section>

<Three to five concrete actions with a trigger or time estimate.>

## Sources

- <Author/Org.> (<year>). *<Title>*. <URL>
  - Supports: <the specific claim this source backs>

## Disclosure

<One to three sentences on AI assistance, human responsibility, and the AUTHOR EXPERIENCE placeholder requirement.>

## <Closing section or paragraph>

<Final question for the reader. Specific enough to answer, open enough to be interesting.>
```

---

## Front-matter field rules

| Field | Rule |
|---|---|
| `title` | Under ~70 characters. Contains the concrete subject ("evaluate", "choose", "pick"), not a platitude. No banned phrases. |
| `subtitle` | States a promise the body actually keeps. Not a restatement of the title. |
| `tags` | 5–8 total. At least one long-tail phrase (e.g. `how-to-evaluate-llm-tools`). At least one domain tag (`ai-evaluation`, `llm`, `data-engineering`). |
| `platform` | `linkedin` (Medium also supported via `medium_publication`). |
| `target_length` | The range the draft aims for, `1000-1800` accepted. |
| `word_count` | Actual body word count. Must land in range. |
| `disclosure` | Matches the standard disclosure language. |
| `rubric_score` | Self-assessed, 0–100, defensible against `rubric.md`. |
| `hard_fail` | `true` or `false`. If `true`, the draft is retained only as a negative example. |
| `distinctness_angle` | One line naming the organizing device, the framing, and the example set. Must be unique across drafts. |
| `sources_count` | Number of distinct URLs in the source list. Minimum 6. |
| `author_experience_placeholders` | Number of `[AUTHOR EXPERIENCE: ...]` markers in the body. |

---

## Placeholder markers

### `[AUTHOR EXPERIENCE: ...]`

The **only** permitted form of first-person material.

```markdown
[AUTHOR EXPERIENCE: Replace with your real account — e.g. the tool you actually evaluated, what you measured, and what you got wrong.]
```

Rules:
- Never fill it in with invented content.
- Never write around it as though you experienced it.
- Keep it in the final article until a human replaces it.
- At least one should appear in the strongest candidate so the human author has a clear seam to fill.

### `[UNVERIFIED]`

Use only for claims traced to S17 or S18, whose contents could not be verified.

```markdown
One bandit-based approach treats prompt selection as an online learning problem rather than offline hyperparameter optimization [UNVERIFIED].
```

Never use `[UNVERIFIED]` as a cover for a claim you simply haven't checked.

---

## Section heading conventions

- Sentence case. `## The leaderboard is a starting point, not an answer`.
- No `## Introduction`, `## Conclusion`, `## Key Takeaways`, `## Summary`.
- Two to six words. Specific enough to be meaningful on their own.
- Headings should state the section's claim, not name its topic. `## Rankings hide the tradeoffs` beats `## The Problem With Rankings`.

---

## Body formatting conventions

- One sentence per line (Medium mobile convention).
- Paragraphs of 1–3 sentences, under ~80 words.
- Bold: at most 3–4 uses in the whole piece, reserved for decision rules.
- Bullets: at most one bulleted list per 300 words; only for genuinely parallel items.
- Tables: at most one, and only if the rows and columns are genuinely parallel.
- Code blocks: avoid. Inline code for identifiers.
- Inline links: put the source name or domain in the sentence so a skimmer knows what they're trusting.

---

## Pre-publication checklist

- [ ] Every inline citation appears in the source list, and every source-list entry is cited inline.
- [ ] Every number matches `sources.md` exactly.
- [ ] Preprint sources are identified as preprints in the limitations section.
- [ ] 2021–2022-era findings (S10, S11, S1, S2) are dated in the body.
- [ ] No banned phrases.
- [ ] No invented first-person claims.
- [ ] AI-assistance disclosure present and specific.
- [ ] `[AUTHOR EXPERIENCE: ...]` placeholders intact and clearly marked.
- [ ] Closing question is answerable by the reader.
- [ ] Word count in 1,000–1,800.
- [ ] Human authorship sign-off obtained before publication.
