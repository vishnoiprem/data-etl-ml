# SignalScribe Editorial Rubric (100 points)

Scoring is per criterion, independently. Each criterion lists its maximum points and what earns full, partial, and zero credit. Every draft carries its self-assessed score in front matter as `rubric_score` and `hard_fail`.

---

## Hard-fail checks (any one = NOT PUBLISHABLE, regardless of total score)

| ID | Check | Why it is disqualifying |
|----|-------|------------------------|
| **HF-1** | Contains any phrase from the Banned Phrases list below. | Marks the piece as machine-slop to a human editor. |
| **HF-2** | Contains an invented first-person experience claim (e.g. "I tested", "in my team we saw", "when I ran"). The only permitted form is a literal `[AUTHOR EXPERIENCE: ...]` placeholder. | Fabrication of firsthand experience. |
| **HF-3** | Contains a fabricated statistic, benchmark number, quote, or URL not present in `research/` and `sources.md`. | Factual fabrication. |
| **HF-4** | Missing the AI-assistance disclosure. | Undisclosed AI authorship. |
| **HF-5** | Missing the source list, or the source list does not correspond to claims actually made in the body. | Orphaned or unbacked evidence. |
| **HF-6** | No closing question for the reader. | The piece does not do its one job on-platform. |
| **HF-7** | No actionable next steps section. | Pure commentary with no utility. |
| **HF-8** | A source is cited as supporting a claim that the recorded research notes say it does **not** support. | Citation misrepresentation. |

---

## Criteria

### 1. Hook & Thesis — 15 points
- **15** — First two lines stop a scrolling reader with a concrete tension, question, or counter-intuitive claim. A one-sentence thesis appears in the first 150 words and is falsifiable.
- **8–14** — Strong opening, thesis present but late or loosely worded.
- **1–7** — Generic opening, thesis implied but never stated.
- **0** — No hook, no thesis.

### 2. Evidence & Citations — 20 points
- **20** — Every load-bearing claim maps to a URL in `sources.md`; the body carries inline attribution; at least 6 distinct sources; the source list matches; numbers are exact to the recorded notes.
- **13–19** — Most claims sourced; 4–5 distinct sources; one minor attribution gap.
- **6–12** — Sourcing is thin or generic; under 4 distinct sources; some claims floating.
- **1–5** — Assertions presented as fact with no support.
- **0** — Sources listed but body claims contradict them, or sources are decorative.

### 3. Technical Accuracy & Depth — 20 points
- **20** — Correct use of mechanism-level detail (why a metric moves, where a benchmark lies), correct terminology, no overstatement, faithful to recorded findings including their caveats.
- **14–19** — Accurate with minor imprecisions.
- **8–13** — Superficial; explains *what* tools exist but not *how* they fail.
- **1–7** — Contains technical errors or misleading simplifications.
- **0** — Fundamentally wrong.

### 4. Practical Utility & Decision Rules — 15 points
- **15** — At least 5 concrete, transferable decision rules or checks; at least 2 worked application examples spanning different roles; a reader could act on this tomorrow without emailing the author.
- **10–14** — 3–4 usable rules; examples present.
- **5–9** — Generic advice ("evaluate carefully").
- **1–4** — Advice with no mechanism.
- **0** — No actionable content.

### 5. Structure & Flow — 10 points
- **10** — Every section earns its place; transitions are logical, not signposted; the piece has a spine a reader can restate in one sentence.
- **7–9** — Good shape; a minor section could be cut or reordered.
- **4–6** — Some drift; sections feel additive rather than sequential.
- **1–3** — Reader loses the thread.
- **0** — No coherent structure.

### 6. Voice & Style (anti-generic-AI) — 8 points
- **8** — Reads like a practitioner writing to peers: short paragraphs, one idea each, active voice, no throat-clearing, varied sentence rhythm, no banned phrasing, concrete nouns.
- **5–7** — Mostly clean; one or two generic paragraphs.
- **3–4** — Multiple generic passages; rhythm uniform.
- **1–2** — Reads as boilerplate.
- **0** — Hard-fail HF-1.

### 7. Ethics & Disclosure — 5 points
- **5** — Clear, specific AI-assistance disclosure; honest treatment of uncertainty and of the limits of evaluation; does not overstate what any benchmark or judge can prove.
- **3–4** — Disclosure present but vague; limits mentioned lightly.
- **1–2** — Disclosure buried or generic.
- **0** — Hard-fail HF-4.

### 8. Title / Subtitle / Tags / SEO — 5 points
- **5** — Title is specific and searchable (contains the concrete subject, not a platitude), subtitle adds a real promise, 5–8 tags including at least one long-tail phrase, front matter complete.
- **3–4** — Adequate title, generic subtitle, tags present.
- **1–2** — Clickbait or vague.
- **0** — Missing front matter.

### 9. Readability — 2 points
- **2** — Target length met (1000–1800 words), paragraphs under ~120 words, headers aid scanning, no paragraph over the platform's comfortable limit.
- **1** — Length off by <15% or a few heavy paragraphs.
- **0** — Length off by ≥15% or unreadable density.

**Total: 15 + 20 + 20 + 15 + 10 + 8 + 5 + 5 + 2 = 100**

---

## Banned Phrases list (HF-1)

Case-insensitive. These strings, and their direct morphological variants, fail the article.

**Core list**
- delve
- game-changer
- unlock the power
- in conclusion
- it's important to note

**Extended AI-slop list**
- in today's fast-paced world
- it is worth noting
- revolutionize
- seamless
- leverage
- robust
- cutting-edge
- ever-evolving landscape
- dive deep
- navigate the landscape
- landscape of
- tapestry
- testament to
- realm of
- in the realm of
- unlock
- supercharge
- skyrocket
- paradigm shift
- at the forefront of
- it's worth mentioning
- without further ado
- picture this
- imagine a world where
- the possibilities are endless
- a testament to
- sits at the intersection of
- paves the way for
- not only … but also
- more than ever before
- in an era where
- fostering
- holistic
- multifaceted
- poised to
- stands as a testament
- moving forward
- ever-growing
- best-in-class
- next-level
- state-of-the-art
- actionability
- synergy
- operationalize

**Banned constructions**
- Paragraphs that open with a rhetorical question and answer it themselves in the next sentence.
- "Not only X, but also Y."
- Three-item bulleted lists where every item starts with the same grammatical form.
- Ending on a grand generalization instead of a question.
- "Whether you're X or Y, Z."
- As an AI, language model, or similar meta-disclaimer in the body (the disclosure line is fine; the meta-paragraph is not).

---

## Score interpretation

| Band | Score | Meaning |
|------|-------|---------|
| A | 90–100 | Strong candidate; publish after human sign-off. |
| B | 80–89 | Publishable with named edits. |
| C | 70–79 | Needs a substantive revision pass. |
| D | 60–69 | Needs a rewrite of at least two sections. |
| F | <60 | Not publishable. |
| **FAIL** | any HF | **Not publishable regardless of score.** |

---

## Draft self-scoring protocol

Each draft records in front matter:

```yaml
rubric_score: 87
hard_fail: false
distinctness_angle: "Three-question filter — authority, age, and fit — applied to papers only"
```

The self-score must be defensible against the criterion definitions above. A draft claiming 95 must have ≥6 distinct cited sources, ≥5 decision rules, and a stated thesis within the first 150 words.
